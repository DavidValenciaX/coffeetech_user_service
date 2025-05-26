import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

import pytest
from unittest.mock import Mock, patch, MagicMock
from domain.services.email_configuration import EmailConfiguration
from domain.services.email_template_service import EmailTemplateService
from domain.services.email_sender_service import EmailSenderService
from domain.services.email_service import EmailService


class TestEmailConfiguration:
    """Test cases for EmailConfiguration."""
    
    def test_email_configuration_creation(self):
        """Test creating EmailConfiguration with all parameters."""
        config = EmailConfiguration(
            smtp_user="test@example.com",
            smtp_pass="password",
            smtp_host="smtp.test.com",
            smtp_port=587,
            app_base_url="http://localhost:8000",
            logo_url="http://localhost:8000/logo.jpg",
            fallback_logo_url="http://fallback.com/logo.jpg"
        )
        
        assert config.smtp_user == "test@example.com"
        assert config.smtp_pass == "password"
        assert config.smtp_host == "smtp.test.com"
        assert config.smtp_port == 587
        assert config.app_base_url == "http://localhost:8000"
        assert config.logo_url == "http://localhost:8000/logo.jpg"
        assert config.fallback_logo_url == "http://fallback.com/logo.jpg"
    
    def test_email_configuration_validation(self):
        """Test EmailConfiguration validation."""
        config = EmailConfiguration(
            smtp_user="test@example.com",
            smtp_pass="password",
            smtp_host="smtp.test.com",
            smtp_port=587,
            app_base_url="http://localhost:8000",
            logo_url="http://localhost:8000/logo.jpg",
            fallback_logo_url="http://fallback.com/logo.jpg"
        )
        
        assert config.validate() is True
        
        # Test invalid configuration
        invalid_config = EmailConfiguration(
            smtp_user="",
            smtp_pass="password",
            smtp_host="smtp.test.com",
            smtp_port=587,
            app_base_url="http://localhost:8000",
            logo_url="http://localhost:8000/logo.jpg",
            fallback_logo_url="http://fallback.com/logo.jpg"
        )
        
        assert invalid_config.validate() is False
    
    @patch.dict('os.environ', {
        'SMTP_USER': 'test@example.com',
        'SMTP_PASS': 'password',
        'APP_BASE_URL': 'http://localhost',
        'PORT': '8000'
    })
    def test_from_environment(self):
        """Test creating EmailConfiguration from environment variables."""
        config = EmailConfiguration.from_environment()
        
        assert config.smtp_user == "test@example.com"
        assert config.smtp_pass == "password"
        assert config.smtp_host == "smtp.zoho.com"
        assert config.smtp_port == 465
        assert config.app_base_url == "http://localhost:8000"


class TestEmailTemplateService:
    """Test cases for EmailTemplateService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = EmailConfiguration(
            smtp_user="test@example.com",
            smtp_pass="password",
            smtp_host="smtp.test.com",
            smtp_port=587,
            app_base_url="http://localhost:8000",
            logo_url="http://localhost:8000/logo.jpg",
            fallback_logo_url="http://fallback.com/logo.jpg"
        )
        self.template_service = EmailTemplateService(self.config)
    
    def test_generate_verification_email(self):
        """Test generating verification email template."""
        token = "123456"
        result = self.template_service.generate_verification_email(token)
        
        assert "subject" in result
        assert "body_html" in result
        assert result["subject"] == "Verificación de Correo Electrónico"
        assert token in result["body_html"]
        assert self.config.logo_url in result["body_html"]
    
    def test_generate_password_reset_email(self):
        """Test generating password reset email template."""
        token = "reset123"
        result = self.template_service.generate_password_reset_email(token)
        
        assert "subject" in result
        assert "body_html" in result
        assert result["subject"] == "Restablecimiento de Contraseña"
        assert token in result["body_html"]
        assert "15 minutos" in result["body_html"]
    
    def test_generate_invitation_email(self):
        """Test generating invitation email template."""
        token = "invite123"
        farm_name = "Test Farm"
        owner_name = "John Doe"
        role = "Worker"
        
        result = self.template_service.generate_invitation_email(token, farm_name, owner_name, role)
        
        assert "subject" in result
        assert "body_html" in result
        assert result["subject"] == "Invitación a CoffeTech"
        assert token in result["body_html"]
        assert farm_name in result["body_html"]
        assert owner_name in result["body_html"]
        assert role in result["body_html"]


class TestEmailSenderService:
    """Test cases for EmailSenderService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = EmailConfiguration(
            smtp_user="test@example.com",
            smtp_pass="password",
            smtp_host="smtp.test.com",
            smtp_port=587,
            app_base_url="http://localhost:8000",
            logo_url="http://localhost:8000/logo.jpg",
            fallback_logo_url="http://fallback.com/logo.jpg"
        )
        self.sender_service = EmailSenderService(self.config)
    
    @patch('domain.services.email_sender_service.smtplib.SMTP_SSL')
    def test_send_email_success(self, mock_smtp):
        """Test successful email sending."""
        # Mock SMTP server
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        result = self.sender_service.send_email(
            email="recipient@example.com",
            subject="Test Subject",
            body_html="<h1>Test Body</h1>"
        )
        
        assert result is True
        mock_smtp.assert_called_once_with(self.config.smtp_host, self.config.smtp_port)
        mock_server.login.assert_called_once_with(self.config.smtp_user, self.config.smtp_pass)
        mock_server.sendmail.assert_called_once()
    
    @patch('domain.services.email_sender_service.smtplib.SMTP_SSL')
    def test_send_email_failure(self, mock_smtp):
        """Test email sending failure."""
        # Mock SMTP server to raise exception
        mock_smtp.side_effect = Exception("SMTP Error")
        
        result = self.sender_service.send_email(
            email="recipient@example.com",
            subject="Test Subject",
            body_html="<h1>Test Body</h1>"
        )
        
        assert result is False
    
    def test_send_template_email(self):
        """Test sending email using template data."""
        template_data = {
            "subject": "Test Subject",
            "body_html": "<h1>Test Body</h1>"
        }
        
        with patch.object(self.sender_service, 'send_email', return_value=True) as mock_send:
            result = self.sender_service.send_template_email("test@example.com", template_data)
            
            assert result is True
            mock_send.assert_called_once_with(
                email="test@example.com",
                subject="Test Subject",
                body_html="<h1>Test Body</h1>"
            )


class TestEmailService:
    """Test cases for the orchestrator EmailService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = EmailConfiguration(
            smtp_user="test@example.com",
            smtp_pass="password",
            smtp_host="smtp.test.com",
            smtp_port=587,
            app_base_url="http://localhost:8000",
            logo_url="http://localhost:8000/logo.jpg",
            fallback_logo_url="http://fallback.com/logo.jpg"
        )
        self.email_service = EmailService(self.config)
    
    def test_send_verification_email(self):
        """Test sending verification email through orchestrator."""
        with patch.object(self.email_service.sender_service, 'send_template_email', return_value=True) as mock_send:
            result = self.email_service.send_verification_email("test@example.com", "123456")
            
            assert result is True
            mock_send.assert_called_once()
    
    def test_send_password_reset_email(self):
        """Test sending password reset email through orchestrator."""
        with patch.object(self.email_service.sender_service, 'send_template_email', return_value=True) as mock_send:
            result = self.email_service.send_password_reset_email("test@example.com", "reset123")
            
            assert result is True
            mock_send.assert_called_once()
    
    def test_send_invitation_email(self):
        """Test sending invitation email through orchestrator."""
        with patch.object(self.email_service.sender_service, 'send_template_email', return_value=True) as mock_send:
            result = self.email_service.send_invitation_email(
                "test@example.com", "invite123", "Test Farm", "John Doe", "Worker"
            )
            
            assert result is True
            mock_send.assert_called_once() 