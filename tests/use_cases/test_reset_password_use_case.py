import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import pytest
import json
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from models.models import Users
from fastapi import HTTPException
from fastapi.responses import ORJSONResponse
from use_cases.reset_password_use_case import ResetPasswordUseCase
from domain.schemas import PasswordReset


class TestResetPasswordUseCase:
    """Test cases for ResetPasswordUseCase."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_user(self):
        """Create a mock user."""
        user = Mock(spec=Users)
        user.user_id = 1
        user.email = "test@example.com"
        user.name = "Test User"
        user.password_hash = "old_hashed_password"
        user.verification_token = "VALID123"
        return user
    
    @pytest.fixture
    def valid_password_reset(self):
        """Create a valid password reset request."""
        return PasswordReset(
            token="VALID123",
            new_password="NewPassword123!",
            confirm_password="NewPassword123!"
        )
    
    @pytest.fixture
    def mismatched_password_reset(self):
        """Create a password reset request with mismatched passwords."""
        return PasswordReset(
            token="VALID123",
            new_password="NewPassword123!",
            confirm_password="DifferentPassword123!"
        )
    
    @pytest.fixture
    def weak_password_reset(self):
        """Create a password reset request with weak password."""
        return PasswordReset(
            token="VALID123",
            new_password="weak",
            confirm_password="weak"
        )
    
    @pytest.fixture
    def invalid_token_reset(self):
        """Create a password reset request with invalid token."""
        return PasswordReset(
            token="INVALID456",
            new_password="NewPassword123!",
            confirm_password="NewPassword123!"
        )
    
    def _extract_response_content(self, response: ORJSONResponse) -> dict:
        """Extract content from ORJSONResponse for testing."""
        if hasattr(response, 'body'):
            return json.loads(response.body.decode())
        # For mock responses, get the content directly
        return response.content if hasattr(response, 'content') else response
    
    @patch('use_cases.reset_password_use_case.UserRepository')
    @patch('use_cases.reset_password_use_case.password_reset_token_service')
    @patch('use_cases.reset_password_use_case.hash_password')
    @patch('use_cases.reset_password_use_case.UserValidator')
    def test_execute_success(self, mock_validator, mock_hash_password, mock_token_service, 
                           mock_user_repository, mock_db, mock_user, valid_password_reset):
        """Test successful password reset."""
        # Arrange
        new_password_hash = "new_hashed_password"
        mock_hash_password.return_value = new_password_hash
        mock_validator.validate_password_strength.return_value = True
        mock_token_service.is_token_valid.return_value = True
        
        mock_repo_instance = mock_user_repository.return_value
        mock_repo_instance.find_by_verification_token.return_value = mock_user
        
        use_case = ResetPasswordUseCase(mock_db)
        
        # Act
        result = use_case.execute(valid_password_reset)
        
        # Assert
        content = self._extract_response_content(result)
        assert content["status"] == "success"
        assert content["message"] == "Contraseña restablecida exitosamente"
        
        # Verify all dependencies were called correctly
        mock_validator.validate_password_strength.assert_called_once_with("NewPassword123!")
        mock_token_service.is_token_valid.assert_called_once_with("VALID123")
        mock_repo_instance.find_by_verification_token.assert_called_once_with("VALID123")
        mock_hash_password.assert_called_once_with("NewPassword123!")
        
        # Verify user password was updated
        assert mock_user.password_hash == new_password_hash
        assert mock_user.verification_token is None
        
        # Verify database operations
        mock_db.commit.assert_called_once()
        mock_token_service.remove_token.assert_called_once_with("VALID123")
    
    @patch('use_cases.reset_password_use_case.UserRepository')
    @patch('use_cases.reset_password_use_case.password_reset_token_service')
    @patch('use_cases.reset_password_use_case.UserValidator')
    def test_execute_passwords_mismatch(self, mock_validator, mock_token_service, 
                                       mock_user_repository, mock_db, mismatched_password_reset):
        """Test password reset with mismatched passwords."""
        # Arrange
        use_case = ResetPasswordUseCase(mock_db)
        
        # Act
        result = use_case.execute(mismatched_password_reset)
        
        # Assert
        content = self._extract_response_content(result)
        assert content["status"] == "error"
        assert content["message"] == "Las contraseñas no coinciden"
        
        # Verify no further processing occurred
        mock_validator.validate_password_strength.assert_not_called()
        mock_token_service.is_token_valid.assert_not_called()
        mock_db.commit.assert_not_called()
    
    @patch('use_cases.reset_password_use_case.UserRepository')
    @patch('use_cases.reset_password_use_case.password_reset_token_service')
    @patch('use_cases.reset_password_use_case.UserValidator')
    def test_execute_weak_password(self, mock_validator, mock_token_service, 
                                  mock_user_repository, mock_db, weak_password_reset):
        """Test password reset with weak password."""
        # Arrange
        mock_validator.validate_password_strength.return_value = False
        
        use_case = ResetPasswordUseCase(mock_db)
        
        # Act
        result = use_case.execute(weak_password_reset)
        
        # Assert
        content = self._extract_response_content(result)
        assert content["status"] == "error"
        assert "La nueva contraseña debe tener al menos 8 caracteres" in content["message"]
        
        # Verify password validation was called but no further processing
        mock_validator.validate_password_strength.assert_called_once_with("weak")
        mock_token_service.is_token_valid.assert_not_called()
        mock_db.commit.assert_not_called()
    
    @patch('use_cases.reset_password_use_case.UserRepository')
    @patch('use_cases.reset_password_use_case.password_reset_token_service')
    @patch('use_cases.reset_password_use_case.UserValidator')
    def test_execute_invalid_token(self, mock_validator, mock_token_service, 
                                  mock_user_repository, mock_db, invalid_token_reset):
        """Test password reset with invalid token."""
        # Arrange
        mock_validator.validate_password_strength.return_value = True
        mock_token_service.is_token_valid.return_value = False
        
        use_case = ResetPasswordUseCase(mock_db)
        
        # Act
        result = use_case.execute(invalid_token_reset)
        
        # Assert
        content = self._extract_response_content(result)
        assert content["status"] == "error"
        assert content["message"] == "Token inválido o expirado"
        
        # Verify token validation was called but no further processing
        mock_validator.validate_password_strength.assert_called_once_with("NewPassword123!")
        mock_token_service.is_token_valid.assert_called_once_with("INVALID456")
        mock_db.commit.assert_not_called()
    
    @patch('use_cases.reset_password_use_case.UserRepository')
    @patch('use_cases.reset_password_use_case.password_reset_token_service')
    @patch('use_cases.reset_password_use_case.UserValidator')
    def test_execute_user_not_found(self, mock_validator, mock_token_service, 
                                   mock_user_repository, mock_db, valid_password_reset):
        """Test password reset when user is not found."""
        # Arrange
        mock_validator.validate_password_strength.return_value = True
        mock_token_service.is_token_valid.return_value = True
        
        mock_repo_instance = mock_user_repository.return_value
        mock_repo_instance.find_by_verification_token.return_value = None
        
        use_case = ResetPasswordUseCase(mock_db)
        
        # Act
        result = use_case.execute(valid_password_reset)
        
        # Assert
        content = self._extract_response_content(result)
        assert content["status"] == "error"
        assert content["message"] == "Usuario no encontrado"
        
        # Verify token validation was called but no database operations
        mock_validator.validate_password_strength.assert_called_once_with("NewPassword123!")
        mock_token_service.is_token_valid.assert_called_once_with("VALID123")
        mock_repo_instance.find_by_verification_token.assert_called_once_with("VALID123")
        mock_db.commit.assert_not_called()
    
    @patch('use_cases.reset_password_use_case.UserRepository')
    @patch('use_cases.reset_password_use_case.password_reset_token_service')
    @patch('use_cases.reset_password_use_case.hash_password')
    @patch('use_cases.reset_password_use_case.UserValidator')
    def test_execute_database_error(self, mock_validator, mock_hash_password, mock_token_service, 
                                   mock_user_repository, mock_db, mock_user, valid_password_reset):
        """Test password reset when database commit fails."""
        # Arrange
        mock_validator.validate_password_strength.return_value = True
        mock_token_service.is_token_valid.return_value = True
        mock_hash_password.return_value = "new_hashed_password"
        
        mock_repo_instance = mock_user_repository.return_value
        mock_repo_instance.find_by_verification_token.return_value = mock_user
        
        mock_db.commit.side_effect = Exception("Database error")
        
        use_case = ResetPasswordUseCase(mock_db)
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            use_case.execute(valid_password_reset)
        
        assert exc_info.value.status_code == 500
        assert "Error al restablecer la contraseña: Database error" in str(exc_info.value.detail)
        
        # Verify rollback was called
        mock_db.rollback.assert_called_once()
    
    @patch('use_cases.reset_password_use_case.UserRepository')
    @patch('use_cases.reset_password_use_case.password_reset_token_service')
    @patch('use_cases.reset_password_use_case.hash_password')
    @patch('use_cases.reset_password_use_case.UserValidator')
    def test_execute_token_service_error(self, mock_validator, mock_hash_password, mock_token_service, 
                                        mock_user_repository, mock_db, mock_user, valid_password_reset):
        """Test password reset when token service fails."""
        # Arrange
        mock_validator.validate_password_strength.return_value = True
        mock_token_service.is_token_valid.return_value = True
        mock_hash_password.return_value = "new_hashed_password"
        
        mock_repo_instance = mock_user_repository.return_value
        mock_repo_instance.find_by_verification_token.return_value = mock_user
        
        mock_token_service.remove_token.side_effect = Exception("Token service error")
        
        use_case = ResetPasswordUseCase(mock_db)
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            use_case.execute(valid_password_reset)
        
        assert exc_info.value.status_code == 500
        assert "Error al restablecer la contraseña: Token service error" in str(exc_info.value.detail)
        
        # Verify rollback was called
        mock_db.rollback.assert_called_once()
    
    def test_passwords_match_private_method(self, mock_db):
        """Test the private _passwords_match method."""
        # Arrange
        use_case = ResetPasswordUseCase(mock_db)
        
        # Act & Assert
        assert use_case._passwords_match("password123", "password123") is True
        assert use_case._passwords_match("password123", "different123") is False
        assert use_case._passwords_match("", "") is True
        assert use_case._passwords_match("password123", "") is False
    
    @patch('use_cases.reset_password_use_case.UserValidator')
    def test_is_password_strong_private_method(self, mock_validator, mock_db):
        """Test the private _is_password_strong method."""
        # Arrange
        mock_validator.validate_password_strength.return_value = True
        use_case = ResetPasswordUseCase(mock_db)
        
        # Act
        result = use_case._is_password_strong("StrongPassword123!")
        
        # Assert
        assert result is True
        mock_validator.validate_password_strength.assert_called_once_with("StrongPassword123!")
    
    @patch('use_cases.reset_password_use_case.password_reset_token_service')
    def test_is_token_valid_private_method(self, mock_token_service, mock_db):
        """Test the private _is_token_valid method."""
        # Arrange
        mock_token_service.is_token_valid.return_value = True
        use_case = ResetPasswordUseCase(mock_db)
        
        # Act
        result = use_case._is_token_valid("VALID123")
        
        # Assert
        assert result is True
        mock_token_service.is_token_valid.assert_called_once_with("VALID123")
    
    @patch('use_cases.reset_password_use_case.UserRepository')
    def test_find_user_by_token_private_method(self, mock_user_repository, mock_db, mock_user):
        """Test the private _find_user_by_token method."""
        # Arrange
        mock_repo_instance = mock_user_repository.return_value
        mock_repo_instance.find_by_verification_token.return_value = mock_user
        
        use_case = ResetPasswordUseCase(mock_db)
        
        # Act
        result = use_case._find_user_by_token("VALID123")
        
        # Assert
        assert result == mock_user
        mock_repo_instance.find_by_verification_token.assert_called_once_with("VALID123")
    
    @patch('use_cases.reset_password_use_case.hash_password')
    def test_update_user_password_private_method(self, mock_hash_password, mock_db, mock_user):
        """Test the private _update_user_password method."""
        # Arrange
        new_password_hash = "new_hashed_password"
        mock_hash_password.return_value = new_password_hash
        
        use_case = ResetPasswordUseCase(mock_db)
        
        # Act
        use_case._update_user_password(mock_user, "NewPassword123!")
        
        # Assert
        assert mock_user.password_hash == new_password_hash
        mock_hash_password.assert_called_once_with("NewPassword123!")
    
    @patch('use_cases.reset_password_use_case.password_reset_token_service')
    def test_cleanup_token_private_method(self, mock_token_service, mock_db, mock_user):
        """Test the private _cleanup_token method."""
        # Arrange
        use_case = ResetPasswordUseCase(mock_db)
        
        # Act
        use_case._cleanup_token(mock_user, "VALID123")
        
        # Assert
        assert mock_user.verification_token is None
        mock_db.commit.assert_called_once()
        mock_token_service.remove_token.assert_called_once_with("VALID123")
    
    @patch('use_cases.reset_password_use_case.UserRepository')
    def test_use_case_initialization(self, mock_user_repository, mock_db):
        """Test that the use case initializes correctly."""
        # Act
        use_case = ResetPasswordUseCase(mock_db)
        
        # Assert
        assert use_case.db == mock_db
        assert use_case.user_repository is not None
        assert use_case.token_service is not None
        mock_user_repository.assert_called_once_with(mock_db)
    
    @patch('use_cases.reset_password_use_case.UserRepository')
    @patch('use_cases.reset_password_use_case.password_reset_token_service')
    @patch('use_cases.reset_password_use_case.UserValidator')
    def test_execute_with_empty_passwords(self, mock_validator, mock_token_service, 
                                         mock_user_repository, mock_db):
        """Test password reset with empty passwords."""
        # Arrange
        empty_password_reset = PasswordReset(
            token="VALID123",
            new_password="",
            confirm_password=""
        )
        
        use_case = ResetPasswordUseCase(mock_db)
        
        # Act
        result = use_case.execute(empty_password_reset)
        
        # Assert
        content = self._extract_response_content(result)
        assert content["status"] == "success"  # Empty passwords match
        
        # But password strength validation should fail
        mock_validator.validate_password_strength.assert_called_once_with("")
    
    @patch('use_cases.reset_password_use_case.UserRepository')
    @patch('use_cases.reset_password_use_case.password_reset_token_service')
    @patch('use_cases.reset_password_use_case.UserValidator')
    def test_execute_with_whitespace_passwords(self, mock_validator, mock_token_service, 
                                              mock_user_repository, mock_db):
        """Test password reset with whitespace passwords."""
        # Arrange
        whitespace_password_reset = PasswordReset(
            token="VALID123",
            new_password="   ",
            confirm_password="   "
        )
        mock_validator.validate_password_strength.return_value = False
        
        use_case = ResetPasswordUseCase(mock_db)
        
        # Act
        result = use_case.execute(whitespace_password_reset)
        
        # Assert
        content = self._extract_response_content(result)
        assert content["status"] == "error"
        assert "La nueva contraseña debe tener al menos 8 caracteres" in content["message"]
    
    @patch('use_cases.reset_password_use_case.UserRepository')
    @patch('use_cases.reset_password_use_case.password_reset_token_service')
    @patch('use_cases.reset_password_use_case.hash_password')
    @patch('use_cases.reset_password_use_case.UserValidator')
    @patch('use_cases.reset_password_use_case.logger')
    def test_logging_behavior_success(self, mock_logger, mock_validator, mock_hash_password, 
                                     mock_token_service, mock_user_repository, mock_db, 
                                     mock_user, valid_password_reset):
        """Test that appropriate logging occurs for successful password reset."""
        # Arrange
        mock_validator.validate_password_strength.return_value = True
        mock_token_service.is_token_valid.return_value = True
        mock_hash_password.return_value = "new_hashed_password"
        
        mock_repo_instance = mock_user_repository.return_value
        mock_repo_instance.find_by_verification_token.return_value = mock_user
        
        use_case = ResetPasswordUseCase(mock_db)
        
        # Act
        use_case.execute(valid_password_reset)
        
        # Assert
        mock_logger.info.assert_any_call("Iniciando el proceso de restablecimiento de contraseña para el token: %s", "VALID123")
        mock_logger.info.assert_any_call("Contraseña restablecida exitosamente para el usuario: %s", mock_user.email)
    
    @patch('use_cases.reset_password_use_case.UserRepository')
    @patch('use_cases.reset_password_use_case.password_reset_token_service')
    @patch('use_cases.reset_password_use_case.UserValidator')
    @patch('use_cases.reset_password_use_case.logger')
    def test_logging_behavior_error(self, mock_logger, mock_validator, mock_token_service, 
                                   mock_user_repository, mock_db, mismatched_password_reset):
        """Test that appropriate logging occurs for password mismatch."""
        # Arrange
        use_case = ResetPasswordUseCase(mock_db)
        
        # Act
        use_case.execute(mismatched_password_reset)
        
        # Assert
        mock_logger.info.assert_called_with("Iniciando el proceso de restablecimiento de contraseña para el token: %s", "VALID123")
        mock_logger.warning.assert_called_with("Las contraseñas no coinciden para el token: %s", "VALID123")
    
    @patch('use_cases.reset_password_use_case.UserRepository')
    @patch('use_cases.reset_password_use_case.password_reset_token_service')
    @patch('use_cases.reset_password_use_case.hash_password')
    @patch('use_cases.reset_password_use_case.UserValidator')
    def test_execute_with_special_characters_in_password(self, mock_validator, mock_hash_password, 
                                                        mock_token_service, mock_user_repository, 
                                                        mock_db, mock_user):
        """Test password reset with special characters in password."""
        # Arrange
        special_password_reset = PasswordReset(
            token="VALID123",
            new_password="P@ssw0rd!#$%^&*()",
            confirm_password="P@ssw0rd!#$%^&*()"
        )
        
        mock_validator.validate_password_strength.return_value = True
        mock_token_service.is_token_valid.return_value = True
        mock_hash_password.return_value = "new_hashed_password"
        
        mock_repo_instance = mock_user_repository.return_value
        mock_repo_instance.find_by_verification_token.return_value = mock_user
        
        use_case = ResetPasswordUseCase(mock_db)
        
        # Act
        result = use_case.execute(special_password_reset)
        
        # Assert
        content = self._extract_response_content(result)
        assert content["status"] == "success"
        assert content["message"] == "Contraseña restablecida exitosamente"
        
        # Verify password with special characters was processed correctly
        mock_hash_password.assert_called_once_with("P@ssw0rd!#$%^&*()")
    
    @patch('use_cases.reset_password_use_case.UserRepository')
    @patch('use_cases.reset_password_use_case.password_reset_token_service')
    @patch('use_cases.reset_password_use_case.hash_password')
    @patch('use_cases.reset_password_use_case.UserValidator')
    def test_execute_with_unicode_characters_in_password(self, mock_validator, mock_hash_password, 
                                                        mock_token_service, mock_user_repository, 
                                                        mock_db, mock_user):
        """Test password reset with unicode characters in password."""
        # Arrange
        unicode_password_reset = PasswordReset(
            token="VALID123",
            new_password="Contraseña123!ñáéíóú",
            confirm_password="Contraseña123!ñáéíóú"
        )
        
        mock_validator.validate_password_strength.return_value = True
        mock_token_service.is_token_valid.return_value = True
        mock_hash_password.return_value = "new_hashed_password"
        
        mock_repo_instance = mock_user_repository.return_value
        mock_repo_instance.find_by_verification_token.return_value = mock_user
        
        use_case = ResetPasswordUseCase(mock_db)
        
        # Act
        result = use_case.execute(unicode_password_reset)
        
        # Assert
        content = self._extract_response_content(result)
        assert content["status"] == "success"
        assert content["message"] == "Contraseña restablecida exitosamente"
        
        # Verify unicode password was processed correctly
        mock_hash_password.assert_called_once_with("Contraseña123!ñáéíóú") 