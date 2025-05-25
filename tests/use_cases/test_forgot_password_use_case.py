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
from use_cases.forgot_password_use_case import ForgotPasswordUseCase
from domain.schemas import PasswordResetRequest
from domain.services import EmailSendError


class TestForgotPasswordUseCase:
    """Test cases for ForgotPasswordUseCase."""
    
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
        user.verification_token = None
        return user
    
    @pytest.fixture
    def password_reset_request(self):
        """Create a password reset request."""
        return PasswordResetRequest(email="test@example.com")
    
    def _extract_response_content(self, response: ORJSONResponse) -> dict:
        """Extract content from ORJSONResponse for testing."""
        if hasattr(response, 'body'):
            return json.loads(response.body.decode())
        # For mock responses, get the content directly
        return response.content if hasattr(response, 'content') else response
    
    @patch('use_cases.forgot_password_use_case.UserRepository')
    @patch('use_cases.forgot_password_use_case.NotificationService')
    @patch('use_cases.forgot_password_use_case.password_reset_token_service')
    @patch('use_cases.forgot_password_use_case.generate_verification_token')
    def test_execute_success(self, mock_generate_token, mock_token_service, 
                           mock_notification_service, mock_user_repository, 
                           mock_db, mock_user, password_reset_request):
        """Test successful password reset request."""
        # Arrange
        generated_token = "ABC123"
        mock_generate_token.return_value = generated_token
        
        mock_repo_instance = mock_user_repository.return_value
        mock_repo_instance.find_by_email.return_value = mock_user
        
        mock_notification_instance = mock_notification_service.return_value
        mock_notification_instance.send_password_reset_email.return_value = None
        
        mock_token_service.store_token.return_value = None
        
        use_case = ForgotPasswordUseCase(mock_db)
        
        # Act
        result = use_case.execute(password_reset_request)
        
        # Assert
        content = self._extract_response_content(result)
        assert content["status"] == "success"
        assert content["message"] == "Correo electrónico de restablecimiento de contraseña enviado"
        
        # Verify all dependencies were called correctly
        mock_repo_instance.find_by_email.assert_called_once_with("test@example.com")
        mock_generate_token.assert_called_once_with(4)
        assert mock_user.verification_token == generated_token
        mock_token_service.store_token.assert_called_once_with(generated_token, "test@example.com", expiration_minutes=15)
        mock_notification_instance.send_password_reset_email.assert_called_once_with("test@example.com", generated_token)
        mock_db.commit.assert_called_once()
    
    @patch('use_cases.forgot_password_use_case.UserRepository')
    @patch('use_cases.forgot_password_use_case.NotificationService')
    @patch('use_cases.forgot_password_use_case.password_reset_token_service')
    @patch('use_cases.forgot_password_use_case.generate_verification_token')
    def test_execute_user_not_found(self, mock_generate_token, mock_token_service, 
                                   mock_notification_service, mock_user_repository, 
                                   mock_db, password_reset_request):
        """Test password reset request with non-existent email."""
        # Arrange
        mock_repo_instance = mock_user_repository.return_value
        mock_repo_instance.find_by_email.return_value = None
        
        use_case = ForgotPasswordUseCase(mock_db)
        
        # Act
        result = use_case.execute(password_reset_request)
        
        # Assert
        content = self._extract_response_content(result)
        assert content["status"] == "error"
        assert content["message"] == "Correo no encontrado"
        
        # Verify only email lookup was called
        mock_repo_instance.find_by_email.assert_called_once_with("test@example.com")
        mock_generate_token.assert_not_called()
        mock_token_service.store_token.assert_not_called()
        mock_db.commit.assert_not_called()
    
    @patch('use_cases.forgot_password_use_case.UserRepository')
    @patch('use_cases.forgot_password_use_case.NotificationService')
    @patch('use_cases.forgot_password_use_case.password_reset_token_service')
    @patch('use_cases.forgot_password_use_case.generate_verification_token')
    def test_execute_email_send_error(self, mock_generate_token, mock_token_service, 
                                     mock_notification_service, mock_user_repository, 
                                     mock_db, mock_user, password_reset_request):
        """Test password reset request when email sending fails."""
        # Arrange
        generated_token = "ABC123"
        mock_generate_token.return_value = generated_token
        
        mock_repo_instance = mock_user_repository.return_value
        mock_repo_instance.find_by_email.return_value = mock_user
        
        mock_notification_instance = mock_notification_service.return_value
        mock_notification_instance.send_password_reset_email.side_effect = EmailSendError("Email service error")
        
        mock_token_service.store_token.return_value = None
        
        use_case = ForgotPasswordUseCase(mock_db)
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            use_case.execute(password_reset_request)
        
        assert exc_info.value.status_code == 500
        assert "Error sending password reset email: Email service error" in str(exc_info.value.detail)
        
        # Verify rollback was called
        mock_db.rollback.assert_called_once()
        
        # Verify token was generated and stored before email failure
        mock_repo_instance.find_by_email.assert_called_once_with("test@example.com")
        mock_generate_token.assert_called_once_with(4)
        mock_token_service.store_token.assert_called_once_with(generated_token, "test@example.com", expiration_minutes=15)
    
    @patch('use_cases.forgot_password_use_case.UserRepository')
    @patch('use_cases.forgot_password_use_case.NotificationService')
    @patch('use_cases.forgot_password_use_case.password_reset_token_service')
    @patch('use_cases.forgot_password_use_case.generate_verification_token')
    def test_execute_token_service_error(self, mock_generate_token, mock_token_service, 
                                        mock_notification_service, mock_user_repository, 
                                        mock_db, mock_user, password_reset_request):
        """Test password reset request when token service fails."""
        # Arrange
        generated_token = "ABC123"
        mock_generate_token.return_value = generated_token
        
        mock_repo_instance = mock_user_repository.return_value
        mock_repo_instance.find_by_email.return_value = mock_user
        
        mock_token_service.store_token.side_effect = Exception("Token service error")
        
        use_case = ForgotPasswordUseCase(mock_db)
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            use_case.execute(password_reset_request)
        
        assert exc_info.value.status_code == 500
        assert "Error sending password reset email: Token service error" in str(exc_info.value.detail)
        
        # Verify rollback was called
        mock_db.rollback.assert_called_once()
    
    @patch('use_cases.forgot_password_use_case.UserRepository')
    @patch('use_cases.forgot_password_use_case.NotificationService')
    @patch('use_cases.forgot_password_use_case.password_reset_token_service')
    @patch('use_cases.forgot_password_use_case.generate_verification_token')
    def test_execute_database_error(self, mock_generate_token, mock_token_service, 
                                   mock_notification_service, mock_user_repository, 
                                   mock_db, mock_user, password_reset_request):
        """Test password reset request when database commit fails."""
        # Arrange
        generated_token = "ABC123"
        mock_generate_token.return_value = generated_token
        
        mock_repo_instance = mock_user_repository.return_value
        mock_repo_instance.find_by_email.return_value = mock_user
        
        mock_token_service.store_token.return_value = None
        mock_db.commit.side_effect = Exception("Database error")
        
        use_case = ForgotPasswordUseCase(mock_db)
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            use_case.execute(password_reset_request)
        
        assert exc_info.value.status_code == 500
        assert "Error sending password reset email: Database error" in str(exc_info.value.detail)
        
        # Verify rollback was called
        mock_db.rollback.assert_called_once()
    
    @patch('use_cases.forgot_password_use_case.UserRepository')
    @patch('use_cases.forgot_password_use_case.NotificationService')
    @patch('use_cases.forgot_password_use_case.password_reset_token_service')
    @patch('use_cases.forgot_password_use_case.generate_verification_token')
    def test_execute_repository_error(self, mock_generate_token, mock_token_service, 
                                     mock_notification_service, mock_user_repository, 
                                     mock_db, password_reset_request):
        """Test password reset request when repository fails."""
        # Arrange
        mock_repo_instance = mock_user_repository.return_value
        mock_repo_instance.find_by_email.side_effect = Exception("Repository error")
        
        use_case = ForgotPasswordUseCase(mock_db)
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            use_case.execute(password_reset_request)
        
        assert exc_info.value.status_code == 500
        assert "Error sending password reset email: Repository error" in str(exc_info.value.detail)
        
        # Verify rollback was called
        mock_db.rollback.assert_called_once()
    
    @patch('use_cases.forgot_password_use_case.UserRepository')
    @patch('use_cases.forgot_password_use_case.NotificationService')
    @patch('use_cases.forgot_password_use_case.password_reset_token_service')
    @patch('use_cases.forgot_password_use_case.generate_verification_token')
    def test_token_generation_and_storage(self, mock_generate_token, mock_token_service, 
                                         mock_notification_service, mock_user_repository, 
                                         mock_db, mock_user, password_reset_request):
        """Test that token generation and storage work correctly."""
        # Arrange
        generated_token = "XYZ789"
        mock_generate_token.return_value = generated_token
        
        mock_repo_instance = mock_user_repository.return_value
        mock_repo_instance.find_by_email.return_value = mock_user
        
        mock_notification_instance = mock_notification_service.return_value
        mock_notification_instance.send_password_reset_email.return_value = None
        
        mock_token_service.store_token.return_value = None
        
        use_case = ForgotPasswordUseCase(mock_db)
        
        # Act
        result = use_case.execute(password_reset_request)
        
        # Assert
        # Verify token was generated with correct length
        mock_generate_token.assert_called_once_with(4)
        
        # Verify token was stored in user object
        assert mock_user.verification_token == generated_token
        
        # Verify token was stored in memory with correct parameters
        mock_token_service.store_token.assert_called_once_with(
            generated_token, 
            "test@example.com", 
            expiration_minutes=15
        )
        
        # Verify success response
        content = self._extract_response_content(result)
        assert content["status"] == "success"
    
    @patch('use_cases.forgot_password_use_case.UserRepository')
    @patch('use_cases.forgot_password_use_case.NotificationService')
    @patch('use_cases.forgot_password_use_case.password_reset_token_service')
    @patch('use_cases.forgot_password_use_case.generate_verification_token')
    def test_private_methods_integration(self, mock_generate_token, mock_token_service, 
                                        mock_notification_service, mock_user_repository, 
                                        mock_db, mock_user, password_reset_request):
        """Test integration of all private methods."""
        # Arrange
        generated_token = "TEST123"
        mock_generate_token.return_value = generated_token
        
        mock_repo_instance = mock_user_repository.return_value
        mock_repo_instance.find_by_email.return_value = mock_user
        
        mock_notification_instance = mock_notification_service.return_value
        mock_notification_instance.send_password_reset_email.return_value = None
        
        mock_token_service.store_token.return_value = None
        
        use_case = ForgotPasswordUseCase(mock_db)
        
        # Act
        result = use_case.execute(password_reset_request)
        
        # Assert - verify the flow of private methods
        # 1. _find_user_by_email was called
        mock_repo_instance.find_by_email.assert_called_once_with("test@example.com")
        
        # 2. _generate_reset_token was called
        mock_generate_token.assert_called_once_with(4)
        
        # 3. _store_reset_token was called (user token updated, memory storage, db commit)
        assert mock_user.verification_token == generated_token
        mock_token_service.store_token.assert_called_once_with(generated_token, "test@example.com", expiration_minutes=15)
        mock_db.commit.assert_called_once()
        
        # 4. _send_reset_email was called
        mock_notification_instance.send_password_reset_email.assert_called_once_with("test@example.com", generated_token)
        
        # 5. Success response returned
        content = self._extract_response_content(result)
        assert content["status"] == "success"
        assert content["message"] == "Correo electrónico de restablecimiento de contraseña enviado"
    
    @patch('use_cases.forgot_password_use_case.UserRepository')
    @patch('use_cases.forgot_password_use_case.NotificationService')
    @patch('use_cases.forgot_password_use_case.password_reset_token_service')
    @patch('use_cases.forgot_password_use_case.generate_verification_token')
    def test_use_case_initialization(self, mock_generate_token, mock_token_service, 
                                    mock_notification_service, mock_user_repository, mock_db):
        """Test that the use case initializes correctly with all dependencies."""
        # Act
        use_case = ForgotPasswordUseCase(mock_db)
        
        # Assert
        assert use_case.db == mock_db
        assert use_case.user_repository is not None
        assert use_case.notification_service is not None
        assert use_case.token_service is not None
        
        # Verify dependencies were instantiated correctly
        mock_user_repository.assert_called_once_with(mock_db)
        mock_notification_service.assert_called_once()
    
    @patch('use_cases.forgot_password_use_case.UserRepository')
    @patch('use_cases.forgot_password_use_case.NotificationService')
    @patch('use_cases.forgot_password_use_case.password_reset_token_service')
    @patch('use_cases.forgot_password_use_case.generate_verification_token')
    def test_execute_with_different_email_formats(self, mock_generate_token, mock_token_service, 
                                                  mock_notification_service, mock_user_repository, 
                                                  mock_db, mock_user):
        """Test password reset with different email formats."""
        # Test cases with different email formats
        test_emails = [
            "user@example.com",
            "user.name@example.com", 
            "user+tag@example.com",
            "user123@example-domain.com"
        ]
        
        for email in test_emails:
            # Arrange
            request = PasswordResetRequest(email=email)
            generated_token = f"TOKEN_{email.split('@')[0]}"
            
            mock_generate_token.return_value = generated_token
            mock_repo_instance = mock_user_repository.return_value
            mock_repo_instance.find_by_email.return_value = mock_user
            
            mock_notification_instance = mock_notification_service.return_value
            mock_notification_instance.send_password_reset_email.return_value = None
            
            mock_token_service.store_token.return_value = None
            
            use_case = ForgotPasswordUseCase(mock_db)
            
            # Act
            result = use_case.execute(request)
            
            # Assert
            content = self._extract_response_content(result)
            assert content["status"] == "success"
            mock_repo_instance.find_by_email.assert_called_with(email)
            mock_token_service.store_token.assert_called_with(generated_token, email, expiration_minutes=15)
            mock_notification_instance.send_password_reset_email.assert_called_with(email, generated_token)
            
            # Reset mocks for next iteration
            mock_repo_instance.reset_mock()
            mock_token_service.reset_mock()
            mock_notification_instance.reset_mock()
            mock_generate_token.reset_mock()
            mock_db.reset_mock() 