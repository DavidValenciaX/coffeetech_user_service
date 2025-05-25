from utils.email import send_email
import logging
import datetime
import pytz
from typing import Dict, Optional

logger = logging.getLogger(__name__)
bogota_tz = pytz.timezone("America/Bogota")

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
            send_email(email, reset_token, 'reset')
            logger.info(f"Email de restablecimiento de contraseña enviado a: {email}")
        except Exception as e:
            logger.error(f"Error al enviar email de restablecimiento a {email}: {str(e)}")
            raise EmailSendError(f"Error al enviar correo de restablecimiento: {str(e)}")


class PasswordResetTokenService:
    """Servicio responsable de gestionar tokens de restablecimiento de contraseña."""
    
    def __init__(self):
        self._reset_tokens: Dict[str, Dict] = {}
    
    def store_token(self, token: str, email: str, expiration_minutes: int = 15) -> None:
        """
        Almacena un token de restablecimiento con su información asociada.
        
        Args:
            token: Token de restablecimiento
            email: Email del usuario
            expiration_minutes: Minutos hasta la expiración del token
        """
        expiration_time = datetime.datetime.now(bogota_tz) + datetime.timedelta(minutes=expiration_minutes)
        
        self._reset_tokens[token] = {
            "expires_at": expiration_time,
            "email": email
        }
        
        logger.info(f"Token de restablecimiento almacenado para el correo: {email}")
        logger.debug(f"Token expira a: {expiration_time}")
    
    def get_token_info(self, token: str) -> Optional[Dict]:
        """
        Obtiene la información de un token de restablecimiento.
        
        Args:
            token: Token de restablecimiento
            
        Returns:
            Información del token o None si no existe
        """
        return self._reset_tokens.get(token)
    
    def is_token_valid(self, token: str) -> bool:
        """
        Verifica si un token es válido y no ha expirado.
        
        Args:
            token: Token de restablecimiento
            
        Returns:
            True si el token es válido, False en caso contrario
        """
        token_info = self.get_token_info(token)
        
        if not token_info:
            logger.warning(f"Token no encontrado: {token}")
            return False
        
        current_time = datetime.datetime.now(bogota_tz)
        expires_at = token_info['expires_at']
        
        if current_time > expires_at:
            logger.info(f"Token expirado: {token}")
            self.remove_token(token)
            return False
        
        return True
    
    def remove_token(self, token: str) -> None:
        """
        Elimina un token del almacenamiento.
        
        Args:
            token: Token a eliminar
        """
        if token in self._reset_tokens:
            del self._reset_tokens[token]
            logger.info(f"Token eliminado: {token}")
    
    def cleanup_expired_tokens(self) -> None:
        """Limpia todos los tokens expirados del almacenamiento."""
        current_time = datetime.datetime.now(bogota_tz)
        expired_tokens = [
            token for token, info in self._reset_tokens.items()
            if current_time > info['expires_at']
        ]
        
        for token in expired_tokens:
            self.remove_token(token)
        
        if expired_tokens:
            logger.info(f"Se eliminaron {len(expired_tokens)} tokens expirados")


# Instancia global del servicio de tokens
password_reset_token_service = PasswordResetTokenService() 