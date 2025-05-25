from typing import Optional
from sqlalchemy.orm import Session
from models.models import Users
from utils.security import hash_password
from domain.services.token_service import generate_verification_token
from domain.user_state_repository import UserStateRepository, UserStateConstants, UserStateNotFoundError
import logging

logger = logging.getLogger(__name__)


class UserRepository:
    """Repositorio responsable de las operaciones de base de datos de usuarios."""
    
    def __init__(self, db: Session):
        self.db = db
        self.user_state_repository = UserStateRepository(db)
    
    def find_by_email(self, email: str) -> Optional[Users]:
        """
        Busca un usuario por email.
        
        Args:
            email: Email del usuario
            
        Returns:
            Usuario encontrado o None
        """
        return self.db.query(Users).filter(Users.email == email).first()
    
    def find_by_verification_token(self, token: str) -> Optional[Users]:
        """
        Busca un usuario por token de verificación.
        
        Args:
            token: Token de verificación
            
        Returns:
            Usuario encontrado o None
        """
        return self.db.query(Users).filter(Users.verification_token == token).first()
    
    def get_user_state_by_name(self, state_name: str):
        """
        Obtiene un estado de usuario por nombre.
        
        Args:
            state_name: Nombre del estado a obtener
            
        Returns:
            Estado de usuario encontrado o None
        """
        return self.user_state_repository.get_user_state_by_name(state_name)
    
    def create_user(self, name: str, email: str, password: str) -> Users:
        """
        Crea un nuevo usuario en la base de datos.
        
        Args:
            name: Nombre del usuario
            email: Email del usuario
            password: Contraseña en texto plano
            
        Returns:
            Usuario creado
            
        Raises:
            Exception: Si hay error al crear el usuario
        """
        try:
            password_hash = hash_password(password)
            verification_token = generate_verification_token(4)
            
            user_registry_state = self.get_user_state_by_name(UserStateConstants.UNVERIFIED)
            if not user_registry_state:
                raise UserStateNotFoundError(f"No se encontró el estado '{UserStateConstants.UNVERIFIED}' para usuarios")
            
            new_user = Users(
                name=name,
                email=email,
                password_hash=password_hash,
                verification_token=verification_token,
                user_state_id=user_registry_state.user_state_id
            )
            
            self.db.add(new_user)
            self.db.commit()
            self.db.refresh(new_user)
            
            logger.info(f"Usuario creado exitosamente: {email}")
            return new_user
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error al crear usuario: {str(e)}")
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
            Exception: Si hay error al actualizar el usuario
        """
        try:
            user.name = name
            user.password_hash = hash_password(password)
            verification_token = generate_verification_token(4)
            user.verification_token = verification_token
            
            self.db.commit()
            self.db.refresh(user)
            
            logger.info(f"Usuario actualizado exitosamente: {user.email}")
            return user
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error al actualizar usuario: {str(e)}")
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
            verified_state = self.get_user_state_by_name(UserStateConstants.VERIFIED)
            if not verified_state:
                raise UserStateNotFoundError(f"No se encontró el estado '{UserStateConstants.VERIFIED}' para usuarios")
            
            user.verification_token = None
            user.user_state_id = verified_state.user_state_id
            
            self.db.commit()
            logger.info(f"Usuario verificado exitosamente: {user.email}")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error al verificar el correo para el usuario {user.email}: {str(e)}")
            raise
    
    def is_user_unverified(self, user: Users) -> bool:
        """
        Verifica si un usuario está en estado 'No Verificado'.
        
        Args:
            user: Usuario a verificar
            
        Returns:
            True si el usuario está no verificado, False en caso contrario
        """
        unverified_state = self.get_user_state_by_name(UserStateConstants.UNVERIFIED)
        return unverified_state and user.user_state_id == unverified_state.user_state_id 