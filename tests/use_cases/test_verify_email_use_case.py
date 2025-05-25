import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import pytest
import json
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from domain.repositories import UserStateNotFoundError
from models.models import Users, UserStates
from fastapi import HTTPException
from fastapi.responses import ORJSONResponse
from use_cases.verify_email_use_case import VerifyEmailUseCase


class TestVerifyEmailUseCase:
    """Test cases for VerifyEmailUseCase."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_user(self):
        """Create a mock user."""
        user = Mock(spec=Users)
        user.email = "test@example.com"
        user.verification_token = "test_token"
        user.user_state_id = 1
        return user
    
    @pytest.fixture
    def mock_verified_state(self):
        """Create a mock verified state."""
        state = Mock(spec=UserStates)
        state.user_state_id = 2
        state.name = "Verificado"
        return state
    
    def _extract_response_content(self, response: ORJSONResponse) -> dict:
        """Extract content from ORJSONResponse for testing."""
        if hasattr(response, 'body'):
            return json.loads(response.body.decode())
        # For mock responses, get the content directly
        return response.content if hasattr(response, 'content') else response
    
    @patch('use_cases.verify_email_use_case.UserRepository')
    @patch('use_cases.verify_email_use_case.NotificationService')
    def test_execute_success(self, mock_notification_service, mock_user_repository, 
                           mock_db, mock_user, mock_verified_state):
        """Test successful email verification."""
        # Arrange
        token = "valid_token"
        mock_repo_instance = mock_user_repository.return_value
        mock_repo_instance.find_by_verification_token.return_value = mock_user
        mock_repo_instance.verify_user_email.return_value = None
        
        mock_notification_instance = mock_notification_service.return_value
        mock_notification_instance.send_welcome_email.return_value = None
        
        use_case = VerifyEmailUseCase(mock_db)
        
        # Act
        result = use_case.execute(token)
        
        # Assert
        content = self._extract_response_content(result)
        assert content["status"] == "success"
        assert content["message"] == "Correo electrónico verificado exitosamente"
        mock_repo_instance.find_by_verification_token.assert_called_once_with(token)
        mock_repo_instance.verify_user_email.assert_called_once_with(mock_user)
        mock_notification_instance.send_welcome_email.assert_called_once_with(mock_user.email)
    
    @patch('use_cases.verify_email_use_case.UserRepository')
    @patch('use_cases.verify_email_use_case.NotificationService')
    def test_execute_invalid_token(self, mock_notification_service, mock_user_repository, mock_db):
        """Test email verification with invalid token."""
        # Arrange
        token = "invalid_token"
        mock_repo_instance = mock_user_repository.return_value
        mock_repo_instance.find_by_verification_token.return_value = None
        
        use_case = VerifyEmailUseCase(mock_db)
        
        # Act
        result = use_case.execute(token)
        
        # Assert
        content = self._extract_response_content(result)
        assert content["status"] == "error"
        assert content["message"] == "Token inválido"
        mock_repo_instance.find_by_verification_token.assert_called_once_with(token)
        mock_repo_instance.verify_user_email.assert_not_called()
    
    @patch('use_cases.verify_email_use_case.UserRepository')
    @patch('use_cases.verify_email_use_case.NotificationService')
    def test_execute_user_state_not_found(self, mock_notification_service, mock_user_repository, 
                                        mock_db, mock_user):
        """Test email verification when verified state is not found."""
        # Arrange
        token = "valid_token"
        mock_repo_instance = mock_user_repository.return_value
        mock_repo_instance.find_by_verification_token.return_value = mock_user
        mock_repo_instance.verify_user_email.side_effect = UserStateNotFoundError(
            "No se encontró el estado 'Verificado' para usuarios"
        )
        
        use_case = VerifyEmailUseCase(mock_db)
        
        # Act
        result = use_case.execute(token)
        
        # Assert
        content = self._extract_response_content(result)
        assert content["status"] == "error"
        assert content["message"] == "No se encontró el estado 'Verificado' para usuarios"
        assert result.status_code == 400
        mock_repo_instance.find_by_verification_token.assert_called_once_with(token)
        mock_repo_instance.verify_user_email.assert_called_once_with(mock_user)
    
    @patch('use_cases.verify_email_use_case.UserRepository')
    @patch('use_cases.verify_email_use_case.NotificationService')
    def test_execute_welcome_email_fails(self, mock_notification_service, mock_user_repository, 
                                       mock_db, mock_user):
        """Test email verification when welcome email fails (should not affect verification)."""
        # Arrange
        token = "valid_token"
        mock_repo_instance = mock_user_repository.return_value
        mock_repo_instance.find_by_verification_token.return_value = mock_user
        mock_repo_instance.verify_user_email.return_value = None
        
        mock_notification_instance = mock_notification_service.return_value
        mock_notification_instance.send_welcome_email.side_effect = Exception("Email service error")
        
        use_case = VerifyEmailUseCase(mock_db)
        
        # Act
        result = use_case.execute(token)
        
        # Assert
        content = self._extract_response_content(result)
        assert content["status"] == "success"
        assert content["message"] == "Correo electrónico verificado exitosamente"
        mock_repo_instance.find_by_verification_token.assert_called_once_with(token)
        mock_repo_instance.verify_user_email.assert_called_once_with(mock_user)
        mock_notification_instance.send_welcome_email.assert_called_once_with(mock_user.email)
    
    @patch('use_cases.verify_email_use_case.UserRepository')
    @patch('use_cases.verify_email_use_case.NotificationService')
    def test_execute_unexpected_error(self, mock_notification_service, mock_user_repository, 
                                    mock_db, mock_user):
        """Test email verification with unexpected error."""
        # Arrange
        token = "valid_token"
        mock_repo_instance = mock_user_repository.return_value
        mock_repo_instance.find_by_verification_token.return_value = mock_user
        mock_repo_instance.verify_user_email.side_effect = Exception("Database error")
        
        use_case = VerifyEmailUseCase(mock_db)
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            use_case.execute(token)
        
        assert exc_info.value.status_code == 500
        assert "Error al verificar el correo: Database error" in str(exc_info.value.detail)
        mock_repo_instance.find_by_verification_token.assert_called_once_with(token)
        mock_repo_instance.verify_user_email.assert_called_once_with(mock_user)
    
    @patch('use_cases.verify_email_use_case.UserRepository')
    @patch('use_cases.verify_email_use_case.NotificationService')
    def test_execute_integration(self, mock_notification_service, mock_user_repository, 
                                mock_db, mock_user):
        """Test integration of the execute method with all dependencies."""
        # Arrange
        token = "valid_token"
        mock_repo_instance = mock_user_repository.return_value
        mock_repo_instance.find_by_verification_token.return_value = mock_user
        mock_repo_instance.verify_user_email.return_value = None
        
        mock_notification_instance = mock_notification_service.return_value
        mock_notification_instance.send_welcome_email.return_value = None
        
        use_case = VerifyEmailUseCase(mock_db)
        
        # Act
        result = use_case.execute(token)
        
        # Assert
        assert isinstance(result, ORJSONResponse)
        content = self._extract_response_content(result)
        assert content["status"] == "success"
        assert content["message"] == "Correo electrónico verificado exitosamente"
        assert result.status_code == 200
        
        # Verify all dependencies were called correctly
        mock_repo_instance.find_by_verification_token.assert_called_once_with(token)
        mock_repo_instance.verify_user_email.assert_called_once_with(mock_user)
        mock_notification_instance.send_welcome_email.assert_called_once_with(mock_user.email) 