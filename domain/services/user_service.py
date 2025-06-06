from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from domain.repositories import UserRepository, UserStateRepository
from domain.repositories.user_state_repository import UserStateConstants, UserStateNotFoundError
from domain.entities.user import User
from domain.entities.user_state import UserState
from utils.security import hash_password
from utils.verification_token import generate_verification_token
from models.models import Users
import logging

logger = logging.getLogger(__name__)

class UserService:
    """Servicio de dominio para la gestión de usuarios."""
    
    USER_NOT_FOUND_DB_ERROR = "Usuario no encontrado en la base de datos"

    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
        self.user_state_repository = UserStateRepository(db)
    
    def create_user(self, name: str, email: str, password: str) -> User:
        """
        Crea un nuevo usuario con toda la lógica de negocio.
        
        Args:
            name: Nombre del usuario
            email: Email del usuario
            password: Contraseña en texto plano
            
        Returns:
            Usuario creado como entidad
            
        Raises:
            UserStateNotFoundError: Si no se encuentra el estado requerido
            Exception: Si hay error al crear el usuario
        """
        try:
            # Verificar si el usuario ya existe
            existing_user_model = self.user_repository.find_by_email(email)
            if existing_user_model:
                existing_user = User.from_model(existing_user_model)
                if existing_user.is_unverified():
                    # Actualizar usuario no verificado
                    return self.update_unverified_user(existing_user, name, password)
                else:
                    raise ValueError(f"Ya existe un usuario con el email: {email}")
            
            # Obtener estado inicial
            user_registry_state = self.user_state_repository.get_user_state_by_name(UserStateConstants.UNVERIFIED)
            if not user_registry_state:
                raise UserStateNotFoundError(f"No se encontró el estado '{UserStateConstants.UNVERIFIED}' para usuarios")
            
            # Crear entidad de usuario
            user_entity = User(
                name=name,
                email=email,
                password_hash=hash_password(password),
                verification_token=generate_verification_token(4),
                user_state=UserState.from_model(user_registry_state)
            )
            
            # Preparar datos del usuario para persistencia
            user_data = {
                'name': user_entity.name,
                'email': user_entity.email,
                'password_hash': user_entity.password_hash,
                'verification_token': user_entity.verification_token,
                'user_state_id': user_registry_state.user_state_id
            }
            
            # Crear en la base de datos y convertir a entidad
            created_user_model = self.user_repository.create(user_data)
            return User.from_model(created_user_model)
            
        except Exception as e:
            logger.error(f"Error en servicio al crear usuario: {str(e)}")
            raise
    
    def update_unverified_user(self, user_entity: User, name: str, password: str) -> User:
        """
        Actualiza un usuario no verificado con nuevos datos.
        
        Args:
            user_entity: Entidad de usuario a actualizar
            name: Nuevo nombre
            password: Nueva contraseña
            
        Returns:
            Usuario actualizado como entidad
            
        Raises:
            ValueError: Si el usuario ya está verificado
            Exception: Si hay error al actualizar el usuario
        """
        try:
            if not user_entity.is_unverified():
                raise ValueError("Solo se pueden actualizar usuarios no verificados")
            
            # Obtener el modelo para actualizar
            user_model = self.user_repository.find_by_id(user_entity.user_id)
            if not user_model:
                raise ValueError(self.USER_NOT_FOUND_DB_ERROR)
            
            # Actualizar la entidad
            user_entity.name = name
            user_entity.password_hash = hash_password(password)
            user_entity.verification_token = generate_verification_token(4)
            
            update_data = {
                'name': user_entity.name,
                'password_hash': user_entity.password_hash,
                'verification_token': user_entity.verification_token
            }
            
            # Actualizar en la base de datos y convertir a entidad
            updated_user_model = self.user_repository.update(user_model, update_data)
            return User.from_model(updated_user_model)
            
        except Exception as e:
            logger.error(f"Error en servicio al actualizar usuario no verificado: {str(e)}")
            raise
    
    def verify_user_email(self, user_entity: User) -> User:
        """
        Marca un usuario como verificado.
        
        Args:
            user_entity: Entidad de usuario a verificar
            
        Returns:
            Usuario verificado como entidad
            
        Raises:
            UserStateNotFoundError: Si no se encuentra el estado verificado
            Exception: Si hay error al actualizar el usuario
        """
        try:
            verified_state = self.user_state_repository.get_user_state_by_name(UserStateConstants.VERIFIED)
            if not verified_state:
                raise UserStateNotFoundError(f"No se encontró el estado '{UserStateConstants.VERIFIED}' para usuarios")
            
            # Obtener el modelo para actualizar
            user_model = self.user_repository.find_by_id(user_entity.user_id)
            if not user_model:
                raise ValueError(self.USER_NOT_FOUND_DB_ERROR)
            
            # Actualizar la entidad
            user_entity.verification_token = None
            user_entity.user_state = UserState.from_model(verified_state)
            
            update_data = {
                'verification_token': None,
                'user_state_id': verified_state.user_state_id
            }
            
            # Actualizar en la base de datos
            updated_user_model = self.user_repository.update(user_model, update_data)
            logger.info(f"Usuario verificado exitosamente: {user_entity.email}")
            
            return User.from_model(updated_user_model)
            
        except Exception as e:
            logger.error(f"Error en servicio al verificar el correo para el usuario {user_entity.email}: {str(e)}")
            raise
    
    def find_user_by_email(self, email: str) -> Optional[User]:
        """
        Busca un usuario por email.
        
        Args:
            email: Email del usuario
            
        Returns:
            Usuario encontrado como entidad o None
        """
        user_model = self.user_repository.find_by_email(email)
        return User.from_model(user_model) if user_model else None
    
    def find_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Busca un usuario por ID.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Usuario encontrado como entidad o None
        """
        user_model = self.user_repository.find_by_id(user_id)
        return User.from_model(user_model) if user_model else None
    
    def find_user_by_verification_token(self, token: str) -> Optional[User]:
        """
        Busca un usuario por token de verificación.
        
        Args:
            token: Token de verificación
            
        Returns:
            Usuario encontrado como entidad o None
        """
        user_model = self.user_repository.find_by_verification_token(token)
        return User.from_model(user_model) if user_model else None
    
    def get_user_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene información básica de un usuario.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Información del usuario si existe, None si no existe
        """
        user_entity = self.find_user_by_id(user_id)
        if user_entity:
            return {
                "user_id": user_entity.user_id,
                "name": user_entity.name,
                "email": user_entity.email,
                "user_state_id": user_entity.user_state.user_state_id if user_entity.user_state else None,
                "is_verified": user_entity.is_verified(),
                "is_suspended": user_entity.is_suspended()
            }
        return None
    
    # Método de compatibilidad para casos donde aún se necesite el modelo
    def _get_user_model_by_entity(self, user_entity: User) -> Optional[Users]:
        """
        Obtiene el modelo SQLAlchemy a partir de una entidad.
        
        Args:
            user_entity: Entidad de usuario
            
        Returns:
            Modelo de usuario o None
        """
        if not user_entity or not user_entity.user_id:
            return None
        return self.user_repository.find_by_id(user_entity.user_id)
    
    def delete_user(self, user_entity: User) -> None:
        """
        Elimina un usuario del sistema.
        
        Args:
            user_entity: Entidad de usuario a eliminar
            
        Raises:
            ValueError: Si el usuario no existe
            Exception: Si hay error al eliminar el usuario
        """
        try:
            if not user_entity or not user_entity.user_id:
                raise ValueError("Usuario inválido para eliminación")
            
            # Obtener el modelo para eliminar
            user_model = self.user_repository.find_by_id(user_entity.user_id)
            if not user_model:
                raise ValueError(self.USER_NOT_FOUND_DB_ERROR)
            
            # Eliminar usando el repositorio
            self.user_repository.delete(user_model)
            logger.info(f"Usuario eliminado exitosamente desde el servicio: {user_entity.email}")
            
        except Exception as e:
            logger.error(f"Error en servicio al eliminar usuario {user_entity.email}: {str(e)}")
            raise 