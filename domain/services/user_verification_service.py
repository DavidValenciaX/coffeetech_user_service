from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from domain.repositories import UserRepository
from domain.services.session_token_service import verify_session_token
from models.models import Users
import logging

logger = logging.getLogger(__name__)

class UserVerificationService:
    """Servicio de dominio para la verificación de usuarios y tokens."""
    
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
    
    def verify_session_token(self, session_token: str) -> Users:
        """
        Verifica si un token de sesión es válido y devuelve el usuario.
        
        Args:
            session_token: Token de sesión a verificar
            
        Returns:
            Usuario correspondiente al token
            
        Raises:
            ValueError: Si el token es inválido o el usuario no existe
            SQLAlchemyError: Si hay error en la base de datos
        """
        try:
            user = verify_session_token(session_token, self.db)
            if not user:
                raise ValueError("Token de sesión inválido o usuario no encontrado")
            
            return user
        except SQLAlchemyError as e:
            logger.error(f"Error verifying session token: {str(e)}")
            raise
    
    def verify_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Verifica si existe un usuario con el email dado.
        
        Args:
            email: Email del usuario a verificar
            
        Returns:
            Información del usuario si existe, None si no existe
            
        Raises:
            SQLAlchemyError: Si hay error en la base de datos
        """
        try:
            user = self.user_repository.find_by_email(email)
            if user:
                return {
                    "user_id": user.user_id,
                    "name": user.name,
                    "email": user.email
                }
            return None
        except SQLAlchemyError as e:
            logger.error(f"Error verifying user by email: {str(e)}")
            raise
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene información de un usuario por su ID.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Información del usuario si existe, None si no existe
            
        Raises:
            SQLAlchemyError: Si hay error en la base de datos
        """
        try:
            user = self.db.query(Users).filter(Users.user_id == user_id).first()
            if user:
                return {
                    "user_id": user.user_id,
                    "name": user.name,
                    "email": user.email
                }
            return None
        except SQLAlchemyError as e:
            logger.error(f"Error getting user by ID: {str(e)}")
            raise 