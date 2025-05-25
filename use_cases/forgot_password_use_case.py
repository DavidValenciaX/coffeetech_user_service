from fastapi import HTTPException
from sqlalchemy.orm import Session
from models.models import Users
from domain.services.token_service import generate_verification_token
from utils.response import create_response
from domain.services import NotificationService, password_reset_token_service
from domain.user_repository import UserRepository
import logging

logger = logging.getLogger(__name__)


class ForgotPasswordUseCase:
    """
    Caso de uso para iniciar el proceso de restablecimiento de contraseña.
    
    Responsabilidades:
    - Validar que el usuario existe
    - Generar token de restablecimiento
    - Almacenar el token en la base de datos y en memoria
    - Enviar email de restablecimiento
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
        self.notification_service = NotificationService()
        self.token_service = password_reset_token_service
    
    def execute(self, request) -> dict:
        """
        Ejecuta el proceso de restablecimiento de contraseña.
        
        Args:
            request: PasswordResetRequest object containing the email
            
        Returns:
            Response object with success or error message
            
        Raises:
            HTTPException: Si hay error durante el proceso
        """
        logger.info("Iniciando el proceso de restablecimiento de contraseña para el correo: %s", request.email)
        
        try:
            # Buscar usuario por email
            user = self._find_user_by_email(request.email)
            if not user:
                logger.warning("Correo no encontrado: %s", request.email)
                return create_response("error", "Correo no encontrado")
            
            # Generar token de restablecimiento
            reset_token = self._generate_reset_token()
            
            # Almacenar token en base de datos y memoria
            self._store_reset_token(user, reset_token, request.email)
            
            # Enviar email de restablecimiento
            self._send_reset_email(request.email, reset_token)
            
            logger.info("Proceso de restablecimiento completado exitosamente para: %s", request.email)
            return create_response("success", "Correo electrónico de restablecimiento de contraseña enviado")
            
        except Exception as e:
            logger.error("Error durante el proceso de restablecimiento de contraseña: %s", str(e))
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Error sending password reset email: {str(e)}")
    
    def _find_user_by_email(self, email: str) -> Users:
        """
        Busca un usuario por email.
        
        Args:
            email: Email del usuario
            
        Returns:
            Usuario encontrado o None
        """
        return self.user_repository.find_by_email(email)
    
    def _generate_reset_token(self) -> str:
        """
        Genera un token único para restablecimiento de contraseña.
        
        Returns:
            Token de restablecimiento generado
        """
        reset_token = generate_verification_token(4)
        logger.info("Token de restablecimiento generado: %s", reset_token)
        return reset_token
    
    def _store_reset_token(self, user: Users, reset_token: str, email: str) -> None:
        """
        Almacena el token en la base de datos y en memoria.
        
        Args:
            user: Usuario al que pertenece el token
            reset_token: Token de restablecimiento
            email: Email del usuario
        """
        # Almacenar en base de datos
        user.verification_token = reset_token
        logger.info("Token de restablecimiento guardado en la base de datos para el usuario: %s", user.email)
        
        # Almacenar en memoria con expiración
        self.token_service.store_token(reset_token, email, expiration_minutes=15)
        
        # Guardar cambios en la base de datos
        self.db.commit()
        logger.info("Cambios guardados en la base de datos para el usuario: %s", user.email)
    
    def _send_reset_email(self, email: str, reset_token: str) -> None:
        """
        Envía el email de restablecimiento de contraseña.
        
        Args:
            email: Email del usuario
            reset_token: Token de restablecimiento
        """
        self.notification_service.send_password_reset_email(email, reset_token)
        logger.info("Correo electrónico de restablecimiento enviado a: %s", email)