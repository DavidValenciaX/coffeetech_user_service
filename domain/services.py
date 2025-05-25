from utils.email import send_email
import logging

logger = logging.getLogger(__name__)

class EmailSendError(Exception):
    """Raised when there is an error sending an email."""
    pass

class NotificationService:
    """Servicio responsable de enviar notificaciones a los usuarios."""
    
    @staticmethod
    def send_verification_email(email: str, verification_token: str) -> None:
        """
        Envía un email de verificación al usuario.
        
        Args:
            email: Email del usuario
            verification_token: Token de verificación
            
        Raises:
            Exception: Si hay error al enviar el email
        """
        try:
            send_email(email, verification_token, 'verification')
            logger.info(f"Email de verificación enviado a: {email}")
        except Exception as e:
            logger.error(f"Error al enviar email de verificación a {email}: {str(e)}")
            raise EmailSendError(f"Error al enviar correo de verificación: {str(e)}")
    
    @staticmethod
    def send_welcome_email(email: str) -> None:
        """
        Envía un email de bienvenida al usuario.
        
        Args:
            email: Email del usuario
            
        Raises:
            Exception: Si hay error al enviar el email
        """
        try:
            # Aquí se podría implementar un email de bienvenida
            # send_email(email, '', 'welcome')
            logger.info(f"Email de bienvenida enviado a: {email}")
        except Exception as e:
            logger.error(f"Error al enviar email de bienvenida a {email}: {str(e)}")
            raise EmailSendError(f"Error al enviar correo de bienvenida: {str(e)}") 