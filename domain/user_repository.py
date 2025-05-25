from typing import Optional
from sqlalchemy.orm import Session
from models.models import Users, UserStates
from utils.security import hash_password
from domain.services.token_service import generate_verification_token
import logging

logger = logging.getLogger(__name__)


def get_user_state(db: Session, state_name: str) -> Optional[UserStates]:
    """
    Obtiene el estado para la entidad Users.
    
    Args:
        db (Session): Sesión de la base de datos.
        state_name (str): Nombre del estado a obtener (e.g., "Activo", "Inactivo", "No Verificado", "Verificado").
        
    Returns:
        El objeto UserStates si se encuentra, None en caso contrario.
    """
    try:
        return db.query(UserStates).filter(UserStates.name == state_name).first()
    except Exception as e:
        logger.error(f"Error al obtener el estado de usuario '{state_name}': {str(e)}")
        return None



class UserStateNotFoundError(Exception):
    """Exception raised when a required user state is not found in the database."""
    pass


class UserRepository:
    """Repositorio responsable de las operaciones de base de datos de usuarios."""
    
    def __init__(self, db: Session):
        self.db = db
    
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
    
    def get_unverified_state(self) -> Optional[UserStates]:
        """
        Obtiene el estado 'No Verificado'.
        
        Returns:
            Estado de usuario no verificado o None
        """
        return get_user_state(self.db, "No Verificado")
    
    def get_verified_state(self) -> Optional[UserStates]:
        """
        Obtiene el estado 'Verificado'.
        
        Returns:
            Estado de usuario verificado o None
        """
        return get_user_state(self.db, "Verificado")
    
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
            
            user_registry_state = self.get_unverified_state()
            if not user_registry_state:
                raise UserStateNotFoundError("No se encontró el estado 'No Verificado' para usuarios")
            
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
            verified_state = self.get_verified_state()
            if not verified_state:
                raise UserStateNotFoundError("No se encontró el estado 'Verificado' para usuarios")
            
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
        unverified_state = self.get_unverified_state()
        return unverified_state and user.user_state_id == unverified_state.user_state_id 