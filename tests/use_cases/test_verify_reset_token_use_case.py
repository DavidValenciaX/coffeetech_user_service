import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import pytest
import json
from unittest.mock import Mock, patch
from fastapi.responses import ORJSONResponse
from use_cases.verify_reset_token_use_case import VerifyResetTokenUseCase


class TestVerifyResetTokenUseCase:
    """Test cases for VerifyResetTokenUseCase."""
    
    @pytest.fixture
    def valid_token(self):
        """Create a valid token for testing."""
        return "VALID123"
    
    @pytest.fixture
    def invalid_token(self):
        """Create an invalid token for testing."""
        return "INVALID456"
    
    @pytest.fixture
    def expired_token(self):
        """Create an expired token for testing."""
        return "EXPIRED789"
    
    def _extract_response_content(self, response: ORJSONResponse) -> dict:
        """Extract content from ORJSONResponse for testing."""
        if hasattr(response, 'body'):
            return json.loads(response.body.decode())
        # For mock responses, get the content directly
        return response.content if hasattr(response, 'content') else response
    
    @patch('use_cases.verify_reset_token_use_case.password_reset_token_service')
    def test_execute_valid_token_success(self, mock_token_service, valid_token):
        """Test successful token verification with valid token."""
        # Arrange
        mock_token_service.is_token_valid.return_value = True
        
        use_case = VerifyResetTokenUseCase()
        
        # Act
        result = use_case.execute(valid_token)
        
        # Assert
        content = self._extract_response_content(result)
        assert content["status"] == "success"
        assert content["message"] == "Token válido. Puede proceder a restablecer la contraseña."
        
        # Verify token service was called correctly
        mock_token_service.is_token_valid.assert_called_once_with(valid_token)
    
    @patch('use_cases.verify_reset_token_use_case.password_reset_token_service')
    def test_execute_invalid_token_error(self, mock_token_service, invalid_token):
        """Test token verification with invalid token."""
        # Arrange
        mock_token_service.is_token_valid.return_value = False
        
        use_case = VerifyResetTokenUseCase()
        
        # Act
        result = use_case.execute(invalid_token)
        
        # Assert
        content = self._extract_response_content(result)
        assert content["status"] == "error"
        assert content["message"] == "Token inválido o expirado"
        
        # Verify token service was called correctly
        mock_token_service.is_token_valid.assert_called_once_with(invalid_token)
    
    @patch('use_cases.verify_reset_token_use_case.password_reset_token_service')
    def test_execute_expired_token_error(self, mock_token_service, expired_token):
        """Test token verification with expired token."""
        # Arrange
        mock_token_service.is_token_valid.return_value = False
        
        use_case = VerifyResetTokenUseCase()
        
        # Act
        result = use_case.execute(expired_token)
        
        # Assert
        content = self._extract_response_content(result)
        assert content["status"] == "error"
        assert content["message"] == "Token inválido o expirado"
        
        # Verify token service was called correctly
        mock_token_service.is_token_valid.assert_called_once_with(expired_token)
    
    @patch('use_cases.verify_reset_token_use_case.password_reset_token_service')
    def test_execute_empty_token(self, mock_token_service):
        """Test token verification with empty token."""
        # Arrange
        empty_token = ""
        mock_token_service.is_token_valid.return_value = False
        
        use_case = VerifyResetTokenUseCase()
        
        # Act
        result = use_case.execute(empty_token)
        
        # Assert
        content = self._extract_response_content(result)
        assert content["status"] == "error"
        assert content["message"] == "Token inválido o expirado"
        
        # Verify token service was called correctly
        mock_token_service.is_token_valid.assert_called_once_with(empty_token)
    
    @patch('use_cases.verify_reset_token_use_case.password_reset_token_service')
    def test_execute_none_token(self, mock_token_service):
        """Test token verification with None token."""
        # Arrange
        none_token = None
        mock_token_service.is_token_valid.return_value = False
        
        use_case = VerifyResetTokenUseCase()
        
        # Act
        result = use_case.execute(none_token)
        
        # Assert
        content = self._extract_response_content(result)
        assert content["status"] == "error"
        assert content["message"] == "Token inválido o expirado"
        
        # Verify token service was called correctly
        mock_token_service.is_token_valid.assert_called_once_with(none_token)
    
    @patch('use_cases.verify_reset_token_use_case.password_reset_token_service')
    def test_is_token_valid_private_method(self, mock_token_service, valid_token):
        """Test the private _is_token_valid method."""
        # Arrange
        mock_token_service.is_token_valid.return_value = True
        
        use_case = VerifyResetTokenUseCase()
        
        # Act
        result = use_case._is_token_valid(valid_token)
        
        # Assert
        assert result is True
        mock_token_service.is_token_valid.assert_called_once_with(valid_token)
    
    @patch('use_cases.verify_reset_token_use_case.password_reset_token_service')
    def test_is_token_valid_private_method_false(self, mock_token_service, invalid_token):
        """Test the private _is_token_valid method returns False."""
        # Arrange
        mock_token_service.is_token_valid.return_value = False
        
        use_case = VerifyResetTokenUseCase()
        
        # Act
        result = use_case._is_token_valid(invalid_token)
        
        # Assert
        assert result is False
        mock_token_service.is_token_valid.assert_called_once_with(invalid_token)
    
    @patch('use_cases.verify_reset_token_use_case.password_reset_token_service')
    def test_get_token_info_success(self, mock_token_service, valid_token):
        """Test getting token info successfully."""
        # Arrange
        expected_token_info = {
            "email": "test@example.com",
            "expires_at": "2024-01-01T12:00:00"
        }
        mock_token_service.get_token_info.return_value = expected_token_info
        
        use_case = VerifyResetTokenUseCase()
        
        # Act
        result = use_case.get_token_info(valid_token)
        
        # Assert
        assert result == expected_token_info
        mock_token_service.get_token_info.assert_called_once_with(valid_token)
    
    @patch('use_cases.verify_reset_token_use_case.password_reset_token_service')
    def test_get_token_info_not_found(self, mock_token_service, invalid_token):
        """Test getting token info for non-existent token."""
        # Arrange
        mock_token_service.get_token_info.return_value = None
        
        use_case = VerifyResetTokenUseCase()
        
        # Act
        result = use_case.get_token_info(invalid_token)
        
        # Assert
        assert result is None
        mock_token_service.get_token_info.assert_called_once_with(invalid_token)
    
    @patch('use_cases.verify_reset_token_use_case.password_reset_token_service')
    def test_token_service_exception_handling(self, mock_token_service, valid_token):
        """Test handling of token service exceptions."""
        # Arrange
        mock_token_service.is_token_valid.side_effect = Exception("Token service error")
        
        use_case = VerifyResetTokenUseCase()
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            use_case.execute(valid_token)
        
        assert "Token service error" in str(exc_info.value)
        mock_token_service.is_token_valid.assert_called_once_with(valid_token)
    
    def test_use_case_initialization(self):
        """Test that the use case initializes correctly."""
        # Act
        use_case = VerifyResetTokenUseCase()
        
        # Assert
        assert use_case.token_service is not None
        assert hasattr(use_case, 'token_service')
    
    @patch('use_cases.verify_reset_token_use_case.password_reset_token_service')
    def test_execute_with_whitespace_token(self, mock_token_service):
        """Test token verification with whitespace token."""
        # Arrange
        whitespace_token = "   "
        mock_token_service.is_token_valid.return_value = False
        
        use_case = VerifyResetTokenUseCase()
        
        # Act
        result = use_case.execute(whitespace_token)
        
        # Assert
        content = self._extract_response_content(result)
        assert content["status"] == "error"
        assert content["message"] == "Token inválido o expirado"
        
        # Verify token service was called correctly
        mock_token_service.is_token_valid.assert_called_once_with(whitespace_token)
    
    @patch('use_cases.verify_reset_token_use_case.password_reset_token_service')
    def test_execute_with_special_characters_token(self, mock_token_service):
        """Test token verification with special characters in token."""
        # Arrange
        special_token = "ABC123!@#$%^&*()"
        mock_token_service.is_token_valid.return_value = True
        
        use_case = VerifyResetTokenUseCase()
        
        # Act
        result = use_case.execute(special_token)
        
        # Assert
        content = self._extract_response_content(result)
        assert content["status"] == "success"
        assert content["message"] == "Token válido. Puede proceder a restablecer la contraseña."
        
        # Verify token service was called correctly
        mock_token_service.is_token_valid.assert_called_once_with(special_token)
    
    @patch('use_cases.verify_reset_token_use_case.password_reset_token_service')
    def test_execute_with_very_long_token(self, mock_token_service):
        """Test token verification with very long token."""
        # Arrange
        long_token = "A" * 1000  # Very long token
        mock_token_service.is_token_valid.return_value = False
        
        use_case = VerifyResetTokenUseCase()
        
        # Act
        result = use_case.execute(long_token)
        
        # Assert
        content = self._extract_response_content(result)
        assert content["status"] == "error"
        assert content["message"] == "Token inválido o expirado"
        
        # Verify token service was called correctly
        mock_token_service.is_token_valid.assert_called_once_with(long_token)
    
    @patch('use_cases.verify_reset_token_use_case.password_reset_token_service')
    @patch('use_cases.verify_reset_token_use_case.logger')
    def test_logging_behavior_valid_token(self, mock_logger, mock_token_service, valid_token):
        """Test that appropriate logging occurs for valid token."""
        # Arrange
        mock_token_service.is_token_valid.return_value = True
        
        use_case = VerifyResetTokenUseCase()
        
        # Act
        use_case.execute(valid_token)
        
        # Assert
        mock_logger.info.assert_any_call("Iniciando la verificación del token: %s", valid_token)
        mock_logger.info.assert_any_call("Token válido, puede proceder a restablecer la contraseña.")
    
    @patch('use_cases.verify_reset_token_use_case.password_reset_token_service')
    @patch('use_cases.verify_reset_token_use_case.logger')
    def test_logging_behavior_invalid_token(self, mock_logger, mock_token_service, invalid_token):
        """Test that appropriate logging occurs for invalid token."""
        # Arrange
        mock_token_service.is_token_valid.return_value = False
        
        use_case = VerifyResetTokenUseCase()
        
        # Act
        use_case.execute(invalid_token)
        
        # Assert
        mock_logger.info.assert_called_with("Iniciando la verificación del token: %s", invalid_token)
        mock_logger.warning.assert_called_with("Token inválido o expirado: %s", invalid_token) 