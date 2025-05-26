import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

import pytest
from unittest.mock import patch
from domain.services import NotificationService, EmailSendError


class TestNotificationService:
    """Tests para la clase NotificationService."""
    
    @patch('domain.services.notification_service.email_service.send_verification_email')
    def test_send_verification_email_success(self, mock_send_email):
        """Test que envía email de verificación exitosamente."""
        # Arrange
        email = "test@example.com"
        token = "verification_token_123"
        mock_send_email.return_value = True
        
        # Act
        NotificationService.send_verification_email(email, token)
        
        # Assert
        mock_send_email.assert_called_once_with(email, token)
    
    @patch('domain.services.notification_service.email_service.send_verification_email')
    def test_send_verification_email_failure(self, mock_send_email):
        """Test que maneja error al enviar email de verificación."""
        # Arrange
        email = "test@example.com"
        token = "verification_token_123"
        mock_send_email.return_value = False
        
        # Act & Assert
        with pytest.raises(EmailSendError, match="Error al enviar correo de verificación"):
            NotificationService.send_verification_email(email, token)
    
    def test_send_welcome_email_success(self):
        """Test que envía email de bienvenida exitosamente."""
        # Arrange
        email = "test@example.com"
        
        # Act
        result = NotificationService.send_welcome_email(email)
        
        # Assert
        assert result is None
    
    @patch('domain.services.notification_service.logger')
    def test_send_welcome_email_logs_info(self, mock_logger):
        """Test que el email de bienvenida registra información."""
        # Arrange
        email = "test@example.com"
        
        # Act
        NotificationService.send_welcome_email(email)
        
        # Assert
        mock_logger.info.assert_called_once_with(f"Email de bienvenida enviado a: {email}") 