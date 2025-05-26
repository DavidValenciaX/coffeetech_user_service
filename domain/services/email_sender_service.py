import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict
import logging
from .email_configuration import EmailConfiguration

logger = logging.getLogger(__name__)


class EmailSenderService:
    """Service responsible for sending emails."""
    
    def __init__(self, config: EmailConfiguration):
        self.config = config
        
        if not self.config.validate():
            logger.error("Email configuration is not valid")
            raise ValueError("Email configuration is not valid")
    
    def send_email(self, email: str, subject: str, body_html: str) -> bool:
        """
        Send an email with the given subject and HTML body.
        
        Args:
            email: Recipient's email address
            subject: Email subject
            body_html: HTML body content
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        # Create email message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.config.smtp_user
        msg["To"] = email
        
        # Add HTML body
        msg.attach(MIMEText(body_html, "html"))
        
        try:
            # Connect to SMTP server using SSL
            with smtplib.SMTP_SSL(self.config.smtp_host, self.config.smtp_port) as server:
                server.login(self.config.smtp_user, self.config.smtp_pass)
                server.sendmail(self.config.smtp_user, email, msg.as_string())
            logger.info(f"Email enviado exitosamente a {email}")
            return True
        except Exception as e:
            logger.error(f"Error al enviar correo a {email}: {e}")
            return False
    
    def send_template_email(self, email: str, template_data: Dict[str, str]) -> bool:
        """
        Send an email using template data.
        
        Args:
            email: Recipient's email address
            template_data: Dictionary containing 'subject' and 'body_html'
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        return self.send_email(
            email=email,
            subject=template_data["subject"],
            body_html=template_data["body_html"]
        ) 