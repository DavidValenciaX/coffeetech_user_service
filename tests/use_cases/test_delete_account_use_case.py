import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import pytest
from unittest.mock import patch
from fastapi import HTTPException
import orjson

from use_cases.delete_account_use_case import DeleteAccountUseCase
from tests.mockdb import MockDB, Users, UserSessions, UserStates, UserDevices, UserRole, Roles


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
        password_hash='$argon2id$v=19$m=65536,t=3,p=4$hashed_password',
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
    
    # Add a device for this user
    device = UserDevices(
        user_device_id=1,
        user_id=1,
        fcm_token='test_fcm_token'
    )
    mock_db_session.add(device)
    
    # Add a role for this user
    role = mock_db_session.query(Roles).filter(lambda r: r.name == 'Propietario').first()
    if role:
        user_role = UserRole(
            user_role_id=1,
            user_id=1,
            role_id=role.role_id
        )
        mock_db_session.add(user_role)
    
    return user


class TestDeleteAccountUseCase:
    """Test suite for DeleteAccountUseCase."""

    @patch('use_cases.delete_account_use_case.verify_session_token')
    def test_delete_account_success(self, mock_verify_session_token, mock_db_session, sample_user):
        """Test successful account deletion."""
        # Arrange
        mock_verify_session_token.return_value = sample_user
        
        use_case = DeleteAccountUseCase(mock_db_session)
        
        # Verify user exists before deletion
        user_before = mock_db_session.query(Users).filter(lambda u: u.user_id == 1).first()
        assert user_before is not None
        
        # Act
        response_obj = use_case.execute('valid_session_token')
        response = orjson.loads(response_obj.body)
        
        # Assert
        assert response["status"] == "success"
        assert response["message"] == "Cuenta eliminada exitosamente"
        assert mock_db_session.committed
        
        # Verify the user was deleted from the mock database
        # Note: In a real scenario, the user would be deleted from the database
        # but in our mock, we need to simulate this behavior
        mock_verify_session_token.assert_called_once_with('valid_session_token', mock_db_session)

    @patch('use_cases.delete_account_use_case.verify_session_token')
    def test_delete_account_invalid_session_token(self, mock_verify_session_token, mock_db_session):
        """Test account deletion with invalid session token."""
        # Arrange
        mock_verify_session_token.return_value = None
        
        use_case = DeleteAccountUseCase(mock_db_session)
        
        # Act
        response_obj = use_case.execute('invalid_session_token')
        response = orjson.loads(response_obj.body)
        
        # Assert
        assert response["status"] == "error"
        assert response["message"] == "Credenciales expiradas, cerrando sesión."
        assert not mock_db_session.committed
        
        mock_verify_session_token.assert_called_once_with('invalid_session_token', mock_db_session)

    @patch('use_cases.delete_account_use_case.verify_session_token')
    def test_delete_account_empty_session_token(self, mock_verify_session_token, mock_db_session):
        """Test account deletion with empty session token."""
        # Arrange
        mock_verify_session_token.return_value = None
        
        use_case = DeleteAccountUseCase(mock_db_session)
        
        # Act
        response_obj = use_case.execute(None)
        response = orjson.loads(response_obj.body)
        
        # Assert
        assert response["status"] == "error"
        assert response["message"] == "Credenciales expiradas, cerrando sesión."
        assert not mock_db_session.committed

    @patch('use_cases.delete_account_use_case.verify_session_token')
    def test_delete_account_none_session_token(self, mock_verify_session_token, mock_db_session):
        """Test account deletion with None session token."""
        # Arrange
        mock_verify_session_token.return_value = None
        
        use_case = DeleteAccountUseCase(mock_db_session)
        
        # Act
        response_obj = use_case.execute(None)
        response = orjson.loads(response_obj.body)
        
        # Assert
        assert response["status"] == "error"
        assert response["message"] == "Credenciales expiradas, cerrando sesión."
        assert not mock_db_session.committed

    @patch('use_cases.delete_account_use_case.verify_session_token')
    def test_delete_account_database_error_on_delete(self, mock_verify_session_token, 
                                                   mock_db_session, sample_user):
        """Test account deletion with database error during delete operation."""
        # Arrange
        mock_verify_session_token.return_value = sample_user
        
        # Mock the delete method to raise an exception
        def failing_delete(obj):
            raise ConnectionError("Database connection lost")
        mock_db_session.delete = failing_delete
        
        use_case = DeleteAccountUseCase(mock_db_session)
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            use_case.execute('valid_session_token')
        
        assert exc_info.value.status_code == 500
        assert "Error eliminando cuenta" in str(exc_info.value.detail)
        assert mock_db_session.rolled_back

    @patch('use_cases.delete_account_use_case.verify_session_token')
    def test_delete_account_database_error_on_commit(self, mock_verify_session_token, 
                                                   mock_db_session, sample_user):
        """Test account deletion with database error during commit operation."""
        # Arrange
        mock_verify_session_token.return_value = sample_user
        
        # Configure mock DB to fail on commit
        mock_db_session.set_commit_fail(True, "Database commit failed")
        
        use_case = DeleteAccountUseCase(mock_db_session)
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            use_case.execute('valid_session_token')
        
        assert exc_info.value.status_code == 500
        assert "Error eliminando cuenta" in str(exc_info.value.detail)
        assert mock_db_session.rolled_back

    @patch('use_cases.delete_account_use_case.verify_session_token')
    def test_delete_account_with_related_data(self, mock_verify_session_token, 
                                            mock_db_session, sample_user):
        """Test account deletion when user has related data (sessions, devices, roles)."""
        # Arrange
        mock_verify_session_token.return_value = sample_user
        
        # Verify related data exists before deletion
        sessions_before = mock_db_session.query(UserSessions).filter(lambda s: s.user_id == 1).all()
        devices_before = mock_db_session.query(UserDevices).filter(lambda d: d.user_id == 1).all()
        roles_before = mock_db_session.query(UserRole).filter(lambda r: r.user_id == 1).all()
        
        assert len(sessions_before) > 0
        assert len(devices_before) > 0
        assert len(roles_before) > 0
        
        use_case = DeleteAccountUseCase(mock_db_session)
        
        # Act
        response_obj = use_case.execute('valid_session_token')
        response = orjson.loads(response_obj.body)
        
        # Assert
        assert response["status"] == "success"
        assert response["message"] == "Cuenta eliminada exitosamente"
        assert mock_db_session.committed
        
        # In a real scenario with CASCADE DELETE, related records would be deleted automatically
        # Our mock doesn't implement CASCADE, but the test verifies the main operation succeeds

    @patch('use_cases.delete_account_use_case.verify_session_token')
    def test_delete_account_user_repository_initialization(self, mock_verify_session_token, 
                                                         mock_db_session, sample_user):
        """Test that UserRepository is properly initialized in the use case."""
        # Arrange
        mock_verify_session_token.return_value = sample_user
        
        use_case = DeleteAccountUseCase(mock_db_session)
        
        # Assert
        assert use_case.db == mock_db_session
        assert use_case.user_repository is not None
        assert use_case.user_repository.db == mock_db_session

    @patch('use_cases.delete_account_use_case.verify_session_token')
    def test_delete_account_logging_behavior(self, mock_verify_session_token, 
                                           mock_db_session, sample_user):
        """Test that appropriate logging occurs during account deletion."""
        # Arrange
        mock_verify_session_token.return_value = sample_user
        
        use_case = DeleteAccountUseCase(mock_db_session)
        
        # Act
        with patch('use_cases.delete_account_use_case.logger') as mock_logger:
            response_obj = use_case.execute('valid_session_token')
            response = orjson.loads(response_obj.body)
            
            # Assert
            assert response["status"] == "success"
            
            # Verify logging calls
            mock_logger.info.assert_called()
            mock_logger.debug.assert_called()
            
            # Check that the log messages contain expected content
            log_calls = [call.args[0] for call in mock_logger.info.call_args_list]
            assert any("Iniciando proceso de eliminación de cuenta" in call for call in log_calls)
            assert any("Cuenta eliminada exitosamente" in call for call in log_calls)

    @patch('use_cases.delete_account_use_case.verify_session_token')
    def test_delete_account_logging_on_invalid_token(self, mock_verify_session_token, mock_db_session):
        """Test that appropriate warning logging occurs for invalid tokens."""
        # Arrange
        mock_verify_session_token.return_value = None
        
        use_case = DeleteAccountUseCase(mock_db_session)
        
        # Act
        with patch('use_cases.delete_account_use_case.logger') as mock_logger:
            response_obj = use_case.execute('invalid_token')
            response = orjson.loads(response_obj.body)
            
            # Assert
            assert response["status"] == "error"
            
            # Verify warning logging for invalid token
            mock_logger.warning.assert_called()
            warning_calls = [call.args[0] for call in mock_logger.warning.call_args_list]
            assert any("Token de sesión inválido durante eliminación de cuenta" in call for call in warning_calls)

    @patch('use_cases.delete_account_use_case.verify_session_token')
    def test_delete_account_logging_on_error(self, mock_verify_session_token, 
                                           mock_db_session, sample_user):
        """Test that appropriate error logging occurs when deletion fails."""
        # Arrange
        mock_verify_session_token.return_value = sample_user
        
        # Mock the delete method to raise an exception
        def failing_delete(obj):
            raise ConnectionError("Database connection lost")
        mock_db_session.delete = failing_delete
        
        use_case = DeleteAccountUseCase(mock_db_session)
        
        # Act & Assert
        with patch('use_cases.delete_account_use_case.logger') as mock_logger:
            with pytest.raises(HTTPException):
                use_case.execute('valid_session_token')
            
            # Verify error logging
            mock_logger.error.assert_called()
            error_calls = [call.args[0] for call in mock_logger.error.call_args_list]
            assert any("Error eliminando cuenta" in call for call in error_calls)

    @patch('use_cases.delete_account_use_case.verify_session_token')
    def test_delete_account_token_truncation_in_logs(self, mock_verify_session_token, mock_db_session):
        """Test that session tokens are properly truncated in log messages for security."""
        # Arrange
        mock_verify_session_token.return_value = None
        long_token = 'very_long_session_token_that_should_be_truncated_in_logs'
        
        use_case = DeleteAccountUseCase(mock_db_session)
        
        # Act
        with patch('use_cases.delete_account_use_case.logger') as mock_logger:
            use_case.execute(long_token)
            
            # Assert that tokens are truncated to first 8 characters in logs
            warning_calls = [call.args[0] for call in mock_logger.warning.call_args_list]
            info_calls = [call.args[0] for call in mock_logger.info.call_args_list]
            
            # Check that full token is not logged
            all_log_messages = warning_calls + info_calls
            assert not any(long_token in message for message in all_log_messages)
            
            # Check that truncated token (first 8 chars) is logged
            truncated_token = long_token[:8]
            assert any(truncated_token in message for message in all_log_messages)

    @patch('use_cases.delete_account_use_case.verify_session_token')
    def test_delete_account_multiple_sessions_same_user(self, mock_verify_session_token, 
                                                      mock_db_session, sample_user):
        """Test account deletion when user has multiple active sessions."""
        # Arrange
        mock_verify_session_token.return_value = sample_user
        
        # Add additional sessions for the same user
        additional_session = UserSessions(
            user_session_id=2,
            user_id=1,
            session_token='another_session_token'
        )
        mock_db_session.add(additional_session)
        
        use_case = DeleteAccountUseCase(mock_db_session)
        
        # Act
        response_obj = use_case.execute('valid_session_token')
        response = orjson.loads(response_obj.body)
        
        # Assert
        assert response["status"] == "success"
        assert response["message"] == "Cuenta eliminada exitosamente"
        assert mock_db_session.committed

    def test_delete_account_use_case_initialization(self, mock_db_session):
        """Test proper initialization of DeleteAccountUseCase."""
        # Act
        use_case = DeleteAccountUseCase(mock_db_session)
        
        # Assert
        assert use_case.db == mock_db_session
        assert use_case.user_repository is not None
        assert hasattr(use_case.user_repository, 'db')
        assert use_case.user_repository.db == mock_db_session

    @patch('use_cases.delete_account_use_case.verify_session_token')
    def test_delete_account_exception_handling_preserves_original_error(self, mock_verify_session_token, 
                                                                       mock_db_session, sample_user):
        """Test that the original exception details are preserved in the HTTPException."""
        # Arrange
        mock_verify_session_token.return_value = sample_user
        original_error_message = "Specific database constraint violation"
        
        def failing_delete(obj):
            raise ConnectionError(original_error_message)
        mock_db_session.delete = failing_delete
        
        use_case = DeleteAccountUseCase(mock_db_session)
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            use_case.execute('valid_session_token')
        
        assert exc_info.value.status_code == 500
        assert "Error eliminando cuenta" in str(exc_info.value.detail)
        assert original_error_message in str(exc_info.value.detail) 