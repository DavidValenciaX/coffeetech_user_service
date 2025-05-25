from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from domain.repositories import UserRepository, UserStateRepository
from domain.repositories.user_state_repository import UserStateConstants, UserStateNotFoundError
from utils.security import hash_password
from utils.verification_token import generate_verification_token
from models.models import Users
import logging

logger = logging.getLogger(__name__)

class UserService:
    """Servicio de dominio para la gestión de usuarios."""
    
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
        self.user_state_repository = UserStateRepository(db)
    
    def create_user(self, name: str, email: str, password: str) -> Users:
        """
        Crea un nuevo usuario con toda la lógica de negocio.
        
        Args:
            name: Nombre del usuario
            email: Email del usuario
            password: Contraseña en texto plano
            
        Returns:
            Usuario creado
            
        Raises:
            UserStateNotFoundError: Si no se encuentra el estado requerido
            Exception: Si hay error al crear el usuario
        """
        try:
            # Verificar si el usuario ya existe
            existing_user = self.user_repository.find_by_email(email)
            if existing_user:
                if self.is_user_unverified(existing_user):
                    # Actualizar usuario no verificado
                    return self.update_unverified_user(existing_user, name, password)
                else:
                    raise ValueError(f"Ya existe un usuario con el email: {email}")
            
            # Obtener estado inicial
            user_registry_state = self.user_state_repository.get_user_state_by_name(UserStateConstants.UNVERIFIED)
            if not user_registry_state:
                raise UserStateNotFoundError(f"No se encontró el estado '{UserStateConstants.UNVERIFIED}' para usuarios")
            
            # Preparar datos del usuario
            user_data = {
                'name': name,
                'email': email,
                'password_hash': hash_password(password),
                'verification_token': generate_verification_token(4),
                'user_state_id': user_registry_state.user_state_id
            }
            
            return self.user_repository.create(user_data)
            
        except Exception as e:
            logger.error(f"Error en servicio al crear usuario: {str(e)}")
            raise
    
    def update_unverified_user(self, user: Users, name: str, password: str) -> Users:
        """
        Actualiza un usuario no verificado con nuevos datos.
        
        Args:
            user: Usuario a actualizar
            name: Nuevo nombre
            password: Nueva contraseña
            
        Returns:
            Usuario actualizado
            
        Raises:
            ValueError: Si el usuario ya está verificado
            Exception: Si hay error al actualizar el usuario
        """
        try:
            if not self.is_user_unverified(user):
                raise ValueError("Solo se pueden actualizar usuarios no verificados")
            
            update_data = {
                'name': name,
                'password_hash': hash_password(password),
                'verification_token': generate_verification_token(4)
            }
            
            return self.user_repository.update(user, update_data)
            
        except Exception as e:
            logger.error(f"Error en servicio al actualizar usuario no verificado: {str(e)}")
            raise
    
    def verify_user_email(self, user: Users) -> None:
        """
        Marca un usuario como verificado.
        
        Args:
            user: Usuario a verificar
            
        Raises:
            UserStateNotFoundError: Si no se encuentra el estado verificado
            Exception: Si hay error al actualizar el usuario
        """
        try:
            verified_state = self.user_state_repository.get_user_state_by_name(UserStateConstants.VERIFIED)
            if not verified_state:
                raise UserStateNotFoundError(f"No se encontró el estado '{UserStateConstants.VERIFIED}' para usuarios")
            
            update_data = {
                'verification_token': None,
                'user_state_id': verified_state.user_state_id
            }
            
            self.user_repository.update(user, update_data)
            logger.info(f"Usuario verificado exitosamente: {user.email}")
            
        except Exception as e:
            logger.error(f"Error en servicio al verificar el correo para el usuario {user.email}: {str(e)}")
            raise
    
    def is_user_unverified(self, user: Users) -> bool:
        """
        Verifica si un usuario está en estado 'No Verificado'.
        
        Args:
            user: Usuario a verificar
            
        Returns:
            True si el usuario está no verificado, False en caso contrario
        """
        unverified_state = self.user_state_repository.get_user_state_by_name(UserStateConstants.UNVERIFIED)
        return unverified_state and user.user_state_id == unverified_state.user_state_id
    
    def find_user_by_email(self, email: str) -> Optional[Users]:
        """
        Busca un usuario por email.
        
        Args:
            email: Email del usuario
            
        Returns:
            Usuario encontrado o None
        """
        return self.user_repository.find_by_email(email)
    
    def find_user_by_id(self, user_id: int) -> Optional[Users]:
        """
        Busca un usuario por ID.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Usuario encontrado o None
        """
        return self.user_repository.find_by_id(user_id)
    
    def find_user_by_verification_token(self, token: str) -> Optional[Users]:
        """
        Busca un usuario por token de verificación.
        
        Args:
            token: Token de verificación
            
        Returns:
            Usuario encontrado o None
        """
        return self.user_repository.find_by_verification_token(token)
    
    def get_user_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene información básica de un usuario.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Información del usuario si existe, None si no existe
        """
        user = self.user_repository.find_by_id(user_id)
        if user:
            return {
                "user_id": user.user_id,
                "name": user.name,
                "email": user.email,
                "user_state_id": user.user_state_id
            }
        return None 