from utils.response import create_response
from domain.services import password_reset_token_service
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class VerifyResetTokenUseCase:
    """
    Caso de uso para verificar la validez de un token de restablecimiento de contraseña.
    
    Responsabilidades:
    - Verificar que el token existe
    - Verificar que el token no ha expirado
    - Retornar el resultado de la verificación
    """
    
    def __init__(self):
        self.token_service = password_reset_token_service
    
    def execute(self, token: Optional[str]) -> dict:
        """
        Verifica si un token de restablecimiento de contraseña es válido y no ha expirado.
        
        Args:
            token: Token de restablecimiento de contraseña a verificar
            
        Returns:
            dict: Respuesta con el resultado de la verificación
        """
        logger.info("Iniciando la verificación del token: %s", token)
        
        # Verificar si el token es válido
        if self._is_token_valid(token):
            logger.info("Token válido, puede proceder a restablecer la contraseña.")
            return create_response("success", "Token válido. Puede proceder a restablecer la contraseña.")
        else:
            logger.warning("Token inválido o expirado: %s", token)
            return create_response("error", "Token inválido o expirado")
    
    def _is_token_valid(self, token: str) -> bool:
        """
        Verifica si un token es válido utilizando el servicio de tokens.
        
        Args:
            token: Token a verificar
            
        Returns:
            bool: True si el token es válido, False en caso contrario
        """
        return self.token_service.is_token_valid(token)
    
    def get_token_info(self, token: str) -> dict:
        """
        Obtiene información detallada sobre un token.
        
        Args:
            token: Token del cual obtener información
            
        Returns:
            dict: Información del token o None si no existe
        """
        return self.token_service.get_token_info(token)