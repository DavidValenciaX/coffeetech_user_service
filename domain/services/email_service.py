import logging
from .email_configuration import EmailConfiguration
from .email_template_service import EmailTemplateService
from .email_sender_service import EmailSenderService

logger = logging.getLogger(__name__)


class EmailService:
    """Orchestrator service for email operations."""
    
    def __init__(self, config: EmailConfiguration = None):
        """
        Initialize EmailService with configuration.
        
        Args:
            config: EmailConfiguration instance. If None, loads from environment.
        """
        if config is None:
            config = EmailConfiguration.from_environment()
        
        self.config = config
        self.template_service = EmailTemplateService(config)
        self.sender_service = EmailSenderService(config)
    
    def send_verification_email(self, email: str, token: str) -> bool:
        """
        Send a verification email to the user.
        
        Args:
            email: User's email address
            token: Verification token
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        template_data = self.template_service.generate_verification_email(token)
        return self.sender_service.send_template_email(email, template_data)
    
    def send_password_reset_email(self, email: str, token: str) -> bool:
        """
        Send a password reset email to the user.
        
        Args:
            email: User's email address
            token: Password reset token
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        template_data = self.template_service.generate_password_reset_email(token)
        return self.sender_service.send_template_email(email, template_data)
    
    def send_invitation_email(self, email: str, token: str, farm_name: str, owner_name: str, role: str) -> bool:
        """
        Send an invitation email to join a farm.
        
        Args:
            email: User's email address
            token: Invitation token
            farm_name: Name of the farm
            owner_name: Name of the farm owner
            role: Suggested role for the invitee
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        template_data = self.template_service.generate_invitation_email(token, farm_name, owner_name, role)
        return self.sender_service.send_template_email(email, template_data)

# Factory function to create email service with default configuration
def create_email_service() -> EmailService:
    """Create an EmailService instance with default configuration from environment."""
    return EmailService()


# Global instance of the email service
email_service = create_email_service() 