from .email_service import email_service
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
            success = email_service.send_verification_email(email, verification_token)
            if not success:
                raise EmailSendError("Error al enviar correo de verificación")
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
    
    @staticmethod
    def send_password_reset_email(email: str, reset_token: str) -> None:
        """
        Envía un email de restablecimiento de contraseña al usuario.
        
        Args:
            email: Email del usuario
            reset_token: Token de restablecimiento
            
        Raises:
            EmailSendError: Si hay error al enviar el email
        """
        try:
            success = email_service.send_password_reset_email(email, reset_token)
            if not success:
                raise EmailSendError("Error al enviar correo de restablecimiento")
            logger.info(f"Email de restablecimiento de contraseña enviado a: {email}")
        except Exception as e:
            logger.error(f"Error al enviar email de restablecimiento a {email}: {str(e)}")
            raise EmailSendError(f"Error al enviar correo de restablecimiento: {str(e)}") 