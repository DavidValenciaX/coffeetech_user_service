import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
import orjson

from use_cases.change_password_use_case import ChangePasswordUseCase
from domain.schemas import PasswordChange
from tests.mockdb import MockDB, Users, UserSessions, UserStates


@pytest.fixture
def mock_db_session():
    """Create a mock database session for testing."""
    db = MockDB()
    return db


@pytest.fixture
def sample_user(mock_db_session):
    """Create a sample verified user for testing."""
    verified_state = mock_db_session.query(UserStates).filter(lambda s: s.name == 'Verificado').first()
    
    user = Users(
        user_id=1,
        name='Test User',
        email='test@example.com',
        password_hash='$argon2id$v=19$m=65536,t=3,p=4$hashed_password',  # Mock hash
        verification_token=None,
        user_state_id=verified_state.user_state_id
    )
    mock_db_session.add(user)
    
    # Add a session for this user
    session = UserSessions(
        user_session_id=1,
        user_id=1,
        session_token='valid_session_token'
    )
    mock_db_session.add(session)
    
    return user


@pytest.fixture
def password_change_request():
    """Create a sample password change request."""
    return PasswordChange(
        current_password='current_password123',
        new_password='NewPassword123!'
    )


class TestChangePasswordUseCase:
    """Test suite for ChangePasswordUseCase."""

    @patch('use_cases.change_password_use_case.verify_session_token')
    @patch('use_cases.change_password_use_case.verify_password')
    @patch('use_cases.change_password_use_case.hash_password')
    def test_change_password_success(self, mock_hash_password, mock_verify_password, 
                                   mock_verify_session_token, mock_db_session, 
                                   sample_user, password_change_request):
        """Test successful password change."""
        # Arrange
        mock_verify_session_token.return_value = sample_user
        mock_verify_password.return_value = True
        mock_hash_password.return_value = 'new_hashed_password'
        
        use_case = ChangePasswordUseCase(mock_db_session)
        
        # Act
        response_obj = use_case.execute(password_change_request, 'valid_session_token')
        response = orjson.loads(response_obj.body)
        
        # Assert
        assert response["status"] == "success"
        assert response["message"] == "Cambio de contraseña exitoso"
        
        # Verify the password was updated
        assert sample_user.password_hash == 'new_hashed_password'
        assert mock_db_session.committed
        
        # Verify all mocks were called correctly
        mock_verify_session_token.assert_called_once_with('valid_session_token', mock_db_session)
        mock_verify_password.assert_called_once_with('current_password123', '$argon2id$v=19$m=65536,t=3,p=4$hashed_password')
        mock_hash_password.assert_called_once_with('NewPassword123!')

    @patch('use_cases.change_password_use_case.verify_session_token')
    def test_change_password_invalid_session_token(self, mock_verify_session_token, 
                                                 mock_db_session, password_change_request):
        """Test password change with invalid session token."""
        # Arrange
        mock_verify_session_token.return_value = None
        
        use_case = ChangePasswordUseCase(mock_db_session)
        
        # Act
        response_obj = use_case.execute(password_change_request, 'invalid_token')
        response = orjson.loads(response_obj.body)
        
        # Assert
        assert response["status"] == "error"
        assert response["message"] == "Credenciales expiradas, cerrando sesión."
        assert not mock_db_session.committed

    @patch('use_cases.change_password_use_case.verify_session_token')
    @patch('use_cases.change_password_use_case.verify_password')
    def test_change_password_incorrect_current_password(self, mock_verify_password, 
                                                      mock_verify_session_token, 
                                                      mock_db_session, sample_user, 
                                                      password_change_request):
        """Test password change with incorrect current password."""
        # Arrange
        mock_verify_session_token.return_value = sample_user
        mock_verify_password.return_value = False
        
        use_case = ChangePasswordUseCase(mock_db_session)
        
        # Act
        response_obj = use_case.execute(password_change_request, 'valid_session_token')
        response = orjson.loads(response_obj.body)
        
        # Assert
        assert response["status"] == "error"
        assert response["message"] == "Credenciales incorrectas"
        assert not mock_db_session.committed

    @patch('use_cases.change_password_use_case.verify_session_token')
    @patch('use_cases.change_password_use_case.verify_password')
    def test_change_password_weak_new_password(self, mock_verify_password, 
                                             mock_verify_session_token, 
                                             mock_db_session, sample_user):
        """Test password change with weak new password."""
        # Arrange
        mock_verify_session_token.return_value = sample_user
        mock_verify_password.return_value = True
        
        weak_password_request = PasswordChange(
            current_password='current_password123',
            new_password='weak'  # Too short, no uppercase, no special chars
        )
        
        use_case = ChangePasswordUseCase(mock_db_session)
        
        # Act
        response_obj = use_case.execute(weak_password_request, 'valid_session_token')
        response = orjson.loads(response_obj.body)
        
        # Assert
        assert response["status"] == "error"
        assert "La contraseña debe tener al menos 8 caracteres" in response["message"]
        assert not mock_db_session.committed

    @patch('use_cases.change_password_use_case.verify_session_token')
    @patch('use_cases.change_password_use_case.verify_password')
    def test_change_password_missing_uppercase(self, mock_verify_password, 
                                             mock_verify_session_token, 
                                             mock_db_session, sample_user):
        """Test password change with password missing uppercase letter."""
        # Arrange
        mock_verify_session_token.return_value = sample_user
        mock_verify_password.return_value = True
        
        weak_password_request = PasswordChange(
            current_password='current_password123',
            new_password='newpassword123!'  # Missing uppercase
        )
        
        use_case = ChangePasswordUseCase(mock_db_session)
        
        # Act
        response_obj = use_case.execute(weak_password_request, 'valid_session_token')
        response = orjson.loads(response_obj.body)
        
        # Assert
        assert response["status"] == "error"
        assert "La contraseña debe incluir al menos una letra mayúscula" in response["message"]
        assert not mock_db_session.committed

    @patch('use_cases.change_password_use_case.verify_session_token')
    @patch('use_cases.change_password_use_case.verify_password')
    def test_change_password_missing_lowercase(self, mock_verify_password, 
                                             mock_verify_session_token, 
                                             mock_db_session, sample_user):
        """Test password change with password missing lowercase letter."""
        # Arrange
        mock_verify_session_token.return_value = sample_user
        mock_verify_password.return_value = True
        
        weak_password_request = PasswordChange(
            current_password='current_password123',
            new_password='NEWPASSWORD123!'  # Missing lowercase
        )
        
        use_case = ChangePasswordUseCase(mock_db_session)
        
        # Act
        response_obj = use_case.execute(weak_password_request, 'valid_session_token')
        response = orjson.loads(response_obj.body)
        
        # Assert
        assert response["status"] == "error"
        assert "La contraseña debe incluir al menos una letra minúscula" in response["message"]
        assert not mock_db_session.committed

    @patch('use_cases.change_password_use_case.verify_session_token')
    @patch('use_cases.change_password_use_case.verify_password')
    def test_change_password_missing_number(self, mock_verify_password, 
                                          mock_verify_session_token, 
                                          mock_db_session, sample_user):
        """Test password change with password missing number."""
        # Arrange
        mock_verify_session_token.return_value = sample_user
        mock_verify_password.return_value = True
        
        weak_password_request = PasswordChange(
            current_password='current_password123',
            new_password='NewPassword!'  # Missing number
        )
        
        use_case = ChangePasswordUseCase(mock_db_session)
        
        # Act
        response_obj = use_case.execute(weak_password_request, 'valid_session_token')
        response = orjson.loads(response_obj.body)
        
        # Assert
        assert response["status"] == "error"
        assert "La contraseña debe incluir al menos un número" in response["message"]
        assert not mock_db_session.committed

    @patch('use_cases.change_password_use_case.verify_session_token')
    @patch('use_cases.change_password_use_case.verify_password')
    def test_change_password_missing_special_char(self, mock_verify_password, 
                                                 mock_verify_session_token, 
                                                 mock_db_session, sample_user):
        """Test password change with password missing special character."""
        # Arrange
        mock_verify_session_token.return_value = sample_user
        mock_verify_password.return_value = True
        
        weak_password_request = PasswordChange(
            current_password='current_password123',
            new_password='NewPassword123'  # Missing special character
        )
        
        use_case = ChangePasswordUseCase(mock_db_session)
        
        # Act
        response_obj = use_case.execute(weak_password_request, 'valid_session_token')
        response = orjson.loads(response_obj.body)
        
        # Assert
        assert response["status"] == "error"
        assert "La contraseña debe incluir al menos un carácter especial" in response["message"]
        assert not mock_db_session.committed

    @patch('use_cases.change_password_use_case.verify_session_token')
    @patch('use_cases.change_password_use_case.verify_password')
    @patch('use_cases.change_password_use_case.hash_password')
    def test_change_password_database_commit_error(self, mock_hash_password, 
                                                  mock_verify_password, 
                                                  mock_verify_session_token, 
                                                  mock_db_session, sample_user, 
                                                  password_change_request):
        """Test password change with database commit error."""
        # Arrange
        mock_verify_session_token.return_value = sample_user
        mock_verify_password.return_value = True
        mock_hash_password.return_value = 'new_hashed_password'
        
        # Configure mock DB to fail on commit
        mock_db_session.set_commit_fail(True, "Database connection lost")
        
        use_case = ChangePasswordUseCase(mock_db_session)
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            use_case.execute(password_change_request, 'valid_session_token')
        
        assert exc_info.value.status_code == 500
        assert "Error al cambiar la contraseña" in str(exc_info.value.detail)
        assert mock_db_session.rolled_back

    @patch('use_cases.change_password_use_case.verify_session_token')
    @patch('use_cases.change_password_use_case.verify_password')
    @patch('use_cases.change_password_use_case.hash_password')
    def test_change_password_hash_generation_error(self, mock_hash_password, 
                                                  mock_verify_password, 
                                                  mock_verify_session_token, 
                                                  mock_db_session, sample_user, 
                                                  password_change_request):
        """Test password change with hash generation error."""
        # Arrange
        mock_verify_session_token.return_value = sample_user
        mock_verify_password.return_value = True
        mock_hash_password.side_effect = Exception("Hash generation failed")
        
        use_case = ChangePasswordUseCase(mock_db_session)
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            use_case.execute(password_change_request, 'valid_session_token')
        
        assert exc_info.value.status_code == 500
        assert "Error al cambiar la contraseña" in str(exc_info.value.detail)
        assert mock_db_session.rolled_back

    def test_validate_session_token_method(self, mock_db_session, sample_user):
        """Test the _validate_session_token method directly."""
        use_case = ChangePasswordUseCase(mock_db_session)
        
        with patch('use_cases.change_password_use_case.verify_session_token') as mock_verify:
            # Test valid token
            mock_verify.return_value = sample_user
            result = use_case._validate_session_token('valid_token')
            assert result == sample_user
            
            # Test invalid token
            mock_verify.return_value = None
            result = use_case._validate_session_token('invalid_token')
            assert result is None

    def test_verify_current_password_method(self, mock_db_session, sample_user):
        """Test the _verify_current_password method directly."""
        use_case = ChangePasswordUseCase(mock_db_session)
        
        with patch('use_cases.change_password_use_case.verify_password') as mock_verify:
            # Test correct password
            mock_verify.return_value = True
            result = use_case._verify_current_password('correct_password', sample_user)
            assert result is True
            
            # Test incorrect password
            mock_verify.return_value = False
            result = use_case._verify_current_password('wrong_password', sample_user)
            assert result is False

    def test_validate_new_password_method(self, mock_db_session):
        """Test the _validate_new_password method directly."""
        use_case = ChangePasswordUseCase(mock_db_session)
        
        # Test valid password
        result = use_case._validate_new_password('ValidPassword123!')
        assert result is None
        
        # Test invalid password
        result = use_case._validate_new_password('weak')
        assert result is not None
        assert "La contraseña debe tener al menos 8 caracteres" in result

    @patch('use_cases.change_password_use_case.hash_password')
    def test_update_user_password_method(self, mock_hash_password, mock_db_session, sample_user):
        """Test the _update_user_password method directly."""
        use_case = ChangePasswordUseCase(mock_db_session)
        mock_hash_password.return_value = 'new_hashed_password'
        
        # Test successful update
        use_case._update_user_password(sample_user, 'NewPassword123!')
        
        assert sample_user.password_hash == 'new_hashed_password'
        assert mock_db_session.committed
        mock_hash_password.assert_called_once_with('NewPassword123!')

    @patch('use_cases.change_password_use_case.hash_password')
    def test_update_user_password_method_with_error(self, mock_hash_password, mock_db_session, sample_user):
        """Test the _update_user_password method with database error."""
        use_case = ChangePasswordUseCase(mock_db_session)
        mock_hash_password.return_value = 'new_hashed_password'
        
        # Configure mock DB to fail on commit
        mock_db_session.set_commit_fail(True, "Database error")
        
        # Test error handling
        with pytest.raises(Exception) as exc_info:
            use_case._update_user_password(sample_user, 'NewPassword123!')
        
        assert "Database error" in str(exc_info.value)
        assert mock_db_session.rolled_back

    @patch('use_cases.change_password_use_case.verify_session_token')
    @patch('use_cases.change_password_use_case.verify_password')
    @patch('use_cases.change_password_use_case.hash_password')
    def test_change_password_edge_case_empty_passwords(self, mock_hash_password, 
                                                     mock_verify_password, 
                                                     mock_verify_session_token, 
                                                     mock_db_session, sample_user):
        """Test password change with empty passwords."""
        # Arrange
        mock_verify_session_token.return_value = sample_user
        mock_verify_password.return_value = True
        
        empty_password_request = PasswordChange(
            current_password='current_password123',
            new_password=''  # Empty password
        )
        
        use_case = ChangePasswordUseCase(mock_db_session)
        
        # Act
        response_obj = use_case.execute(empty_password_request, 'valid_session_token')
        response = orjson.loads(response_obj.body)
        
        # Assert
        assert response["status"] == "error"
        assert "La contraseña debe tener al menos 8 caracteres" in response["message"]
        assert not mock_db_session.committed

    @patch('use_cases.change_password_use_case.verify_session_token')
    @patch('use_cases.change_password_use_case.verify_password')
    @patch('use_cases.change_password_use_case.hash_password')
    def test_change_password_with_unicode_characters(self, mock_hash_password, 
                                                   mock_verify_password, 
                                                   mock_verify_session_token, 
                                                   mock_db_session, sample_user):
        """Test password change with unicode characters in password."""
        # Arrange
        mock_verify_session_token.return_value = sample_user
        mock_verify_password.return_value = True
        mock_hash_password.return_value = 'new_hashed_password'
        
        unicode_password_request = PasswordChange(
            current_password='current_password123',
            new_password='Contraseña123!'  # Contains unicode characters
        )
        
        use_case = ChangePasswordUseCase(mock_db_session)
        
        # Act
        response_obj = use_case.execute(unicode_password_request, 'valid_session_token')
        response = orjson.loads(response_obj.body)
        
        # Assert
        assert response["status"] == "success"
        assert response["message"] == "Cambio de contraseña exitoso"
        assert mock_db_session.committed 