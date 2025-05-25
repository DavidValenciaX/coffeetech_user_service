from fastapi import HTTPException
from sqlalchemy.orm import Session
from models.models import Users
from utils.security import hash_password
from utils.response import create_response
from domain.validators import UserValidator
from domain.services import password_reset_token_service
from domain.user_repository import UserRepository
import logging

logger = logging.getLogger(__name__)


class ResetPasswordUseCase:
    """
    Caso de uso para restablecer la contraseña de un usuario usando un token válido.
    
    Responsabilidades:
    - Validar que las contraseñas coincidan
    - Validar la fortaleza de la nueva contraseña
    - Verificar la validez del token
    - Actualizar la contraseña del usuario
    - Limpiar el token después del uso
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
        self.token_service = password_reset_token_service
    
    def execute(self, reset) -> dict:
        """
        Restablece la contraseña del usuario usando un token válido.
        
        Args:
            reset: PasswordReset object containing token, new_password, and confirm_password
            
        Returns:
            Response object with success or error message
            
        Raises:
            HTTPException: Si hay error durante el proceso
        """
        logger.info("Iniciando el proceso de restablecimiento de contraseña para el token: %s", reset.token)
        
        try:
            # Validar que las contraseñas coincidan
            if not self._passwords_match(reset.new_password, reset.confirm_password):
                logger.warning("Las contraseñas no coinciden para el token: %s", reset.token)
                return create_response("error", "Las contraseñas no coinciden")
            
            # Validar fortaleza de la nueva contraseña
            if not self._is_password_strong(reset.new_password):
                return create_response("error", "La nueva contraseña debe tener al menos 8 caracteres, incluir una letra mayúscula, una letra minúscula, un número y un carácter especial")
            
            # Verificar validez del token
            if not self._is_token_valid(reset.token):
                logger.warning("Token inválido o expirado: %s", reset.token)
                return create_response("error", "Token inválido o expirado")
            
            # Buscar usuario por token
            user = self._find_user_by_token(reset.token)
            if not user:
                logger.warning("Usuario no encontrado para el token: %s", reset.token)
                return create_response("error", "Usuario no encontrado")
            
            # Actualizar contraseña
            self._update_user_password(user, reset.new_password)
            
            # Limpiar token
            self._cleanup_token(user, reset.token)
            
            logger.info("Contraseña restablecida exitosamente para el usuario: %s", user.email)
            return create_response("success", "Contraseña restablecida exitosamente")
            
        except Exception as e:
            logger.error("Error al restablecer la contraseña: %s", str(e))
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Error al restablecer la contraseña: {str(e)}")
    
    def _passwords_match(self, password: str, confirm_password: str) -> bool:
        """
        Verifica que las contraseñas coincidan.
        
        Args:
            password: Contraseña nueva
            confirm_password: Confirmación de contraseña
            
        Returns:
            bool: True si coinciden, False en caso contrario
        """
        return password == confirm_password
    
    def _is_password_strong(self, password: str) -> bool:
        """
        Valida la fortaleza de la contraseña.
        
        Args:
            password: Contraseña a validar
            
        Returns:
            bool: True si la contraseña es fuerte, False en caso contrario
        """
        return UserValidator.validate_password_strength(password)
    
    def _is_token_valid(self, token: str) -> bool:
        """
        Verifica si el token es válido y no ha expirado.
        
        Args:
            token: Token a verificar
            
        Returns:
            bool: True si el token es válido, False en caso contrario
        """
        return self.token_service.is_token_valid(token)
    
    def _find_user_by_token(self, token: str) -> Users:
        """
        Busca un usuario por su token de verificación.
        
        Args:
            token: Token de verificación
            
        Returns:
            Usuario encontrado o None
        """
        return self.user_repository.find_by_verification_token(token)
    
    def _update_user_password(self, user: Users, new_password: str) -> None:
        """
        Actualiza la contraseña del usuario.
        
        Args:
            user: Usuario a actualizar
            new_password: Nueva contraseña en texto plano
        """
        new_password_hash = hash_password(new_password)
        logger.debug("Hash de la nueva contraseña generado para el usuario: %s", user.email)
        
        user.password_hash = new_password_hash
        logger.info("Contraseña actualizada para el usuario: %s", user.email)
    
    def _cleanup_token(self, user: Users, token: str) -> None:
        """
        Limpia el token después de usarlo.
        
        Args:
            user: Usuario al que pertenece el token
            token: Token a limpiar
        """
        # Limpiar token de la base de datos
        user.verification_token = None
        
        # Confirmar cambios en la base de datos
        self.db.commit()
        logger.info("Cambios confirmados en la base de datos para el usuario: %s", user.email)
        
        # Eliminar token del servicio de tokens
        self.token_service.remove_token(token)
        logger.info("Token eliminado del servicio de tokens: %s", token)