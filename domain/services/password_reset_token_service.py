import logging
import datetime
import pytz
from typing import Dict, Optional

logger = logging.getLogger(__name__)
bogota_tz = pytz.timezone("America/Bogota")

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