from typing import Optional
from sqlalchemy.orm import Session, joinedload
from models.models import Users, UserRole
import logging

logger = logging.getLogger(__name__)

class UserRepository:
    """Repositorio responsable únicamente de las operaciones de persistencia de usuarios."""
    
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
        return self.db.query(Users).options(
            joinedload(Users.user_state),
            joinedload(Users.roles).joinedload(UserRole.role),
            joinedload(Users.sessions),
            joinedload(Users.devices)
        ).filter(Users.email == email).first()
    
    def find_by_id(self, user_id: int) -> Optional[Users]:
        """
        Busca un usuario por ID.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Usuario encontrado o None
        """
        return self.db.query(Users).options(
            joinedload(Users.user_state),
            joinedload(Users.roles).joinedload(UserRole.role),
            joinedload(Users.sessions),
            joinedload(Users.devices)
        ).filter(Users.user_id == user_id).first()
    
    def find_by_verification_token(self, token: str) -> Optional[Users]:
        """
        Busca un usuario por token de verificación.
        
        Args:
            token: Token de verificación
            
        Returns:
            Usuario encontrado o None
        """
        return self.db.query(Users).options(
            joinedload(Users.user_state),
            joinedload(Users.roles).joinedload(UserRole.role),
            joinedload(Users.sessions),
            joinedload(Users.devices)
        ).filter(Users.verification_token == token).first()
    
    def create(self, user_data: dict) -> Users:
        """
        Crea un nuevo usuario en la base de datos.
        
        Args:
            user_data: Diccionario con los datos del usuario
            
        Returns:
            Usuario creado con todas las relaciones cargadas
            
        Raises:
            Exception: Si hay error al crear el usuario
        """
        try:
            new_user = Users(**user_data)
            self.db.add(new_user)
            self.db.commit()
            self.db.refresh(new_user)
            
            # Recargar el usuario con todas las relaciones
            created_user = self.find_by_id(new_user.user_id)
            
            logger.info(f"Usuario creado exitosamente: {user_data.get('email')}")
            return created_user
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error al crear usuario: {str(e)}")
            raise
    
    def update(self, user: Users, update_data: dict) -> Users:
        """
        Actualiza un usuario con nuevos datos.
        
        Args:
            user: Usuario a actualizar
            update_data: Diccionario con los datos a actualizar
            
        Returns:
            Usuario actualizado con todas las relaciones cargadas
            
        Raises:
            Exception: Si hay error al actualizar el usuario
        """
        try:
            for key, value in update_data.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            
            self.db.commit()
            self.db.refresh(user)
            
            # Recargar el usuario con todas las relaciones
            updated_user = self.find_by_id(user.user_id)
            
            logger.info(f"Usuario actualizado exitosamente: {user.email}")
            return updated_user
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error al actualizar usuario: {str(e)}")
            raise
    
    def delete(self, user: Users) -> None:
        """
        Elimina un usuario de la base de datos.
        
        Args:
            user: Usuario a eliminar
            
        Raises:
            Exception: Si hay error al eliminar el usuario
        """
        try:
            self.db.delete(user)
            self.db.commit()
            logger.info(f"Usuario eliminado exitosamente: {user.email}")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error al eliminar usuario: {str(e)}")
            raise 