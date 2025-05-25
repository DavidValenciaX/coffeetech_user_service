from typing import Optional, List
from sqlalchemy.orm import Session
from models.models import UserRole, Roles, Users
import logging

logger = logging.getLogger(__name__)

class UserRoleRepository:
    """Repositorio responsable de las operaciones de base de datos de UserRole."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_user_id(self, user_id: int) -> List[UserRole]:
        """
        Obtiene todos los UserRole de un usuario.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Lista de UserRole del usuario
        """
        return self.db.query(UserRole).filter(UserRole.user_id == user_id).all()
    
    def get_by_id(self, user_role_id: int) -> Optional[UserRole]:
        """
        Obtiene un UserRole por su ID.
        
        Args:
            user_role_id: ID del UserRole
            
        Returns:
            UserRole encontrado o None
        """
        return self.db.query(UserRole).filter(UserRole.user_role_id == user_role_id).first()
    
    def get_by_user_and_role(self, user_id: int, role_id: int) -> Optional[UserRole]:
        """
        Obtiene un UserRole por user_id y role_id.
        
        Args:
            user_id: ID del usuario
            role_id: ID del rol
            
        Returns:
            UserRole encontrado o None
        """
        return self.db.query(UserRole).filter(
            UserRole.user_id == user_id,
            UserRole.role_id == role_id
        ).first()
    
    def get_role_by_name(self, role_name: str) -> Optional[Roles]:
        """
        Obtiene un rol por su nombre.
        
        Args:
            role_name: Nombre del rol
            
        Returns:
            Rol encontrado o None
        """
        return self.db.query(Roles).filter(Roles.name == role_name).first()
    
    def get_role_by_id(self, role_id: int) -> Optional[Roles]:
        """
        Obtiene un rol por su ID.
        
        Args:
            role_id: ID del rol
            
        Returns:
            Rol encontrado o None
        """
        return self.db.query(Roles).filter(Roles.role_id == role_id).first()
    
    def get_user_by_id(self, user_id: int) -> Optional[Users]:
        """
        Obtiene un usuario por su ID.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Usuario encontrado o None
        """
        return self.db.query(Users).filter(Users.user_id == user_id).first()
    
    def create(self, user_id: int, role_id: int) -> UserRole:
        """
        Crea una nueva relación UserRole.
        
        Args:
            user_id: ID del usuario
            role_id: ID del rol
            
        Returns:
            UserRole creado
            
        Raises:
            Exception: Si hay error al crear el UserRole
        """
        try:
            user_role = UserRole(user_id=user_id, role_id=role_id)
            self.db.add(user_role)
            self.db.commit()
            self.db.refresh(user_role)
            logger.info(f"UserRole creado: user_id={user_id}, role_id={role_id}")
            return user_role
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error al crear UserRole: {str(e)}")
            raise
    
    def update_role(self, user_role: UserRole, new_role_id: int) -> UserRole:
        """
        Actualiza el rol de un UserRole.
        
        Args:
            user_role: UserRole a actualizar
            new_role_id: Nuevo ID del rol
            
        Returns:
            UserRole actualizado
            
        Raises:
            Exception: Si hay error al actualizar el UserRole
        """
        try:
            user_role.role_id = new_role_id
            self.db.commit()
            self.db.refresh(user_role)
            logger.info(f"UserRole actualizado: user_role_id={user_role.user_role_id}, new_role_id={new_role_id}")
            return user_role
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error al actualizar UserRole: {str(e)}")
            raise
    
    def delete(self, user_role: UserRole) -> None:
        """
        Elimina un UserRole.
        
        Args:
            user_role: UserRole a eliminar
            
        Raises:
            Exception: Si hay error al eliminar el UserRole
        """
        try:
            self.db.delete(user_role)
            self.db.commit()
            logger.info(f"UserRole eliminado: user_role_id={user_role.user_role_id}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error al eliminar UserRole: {str(e)}")
            raise
    
    def get_multiple_by_ids(self, user_role_ids: List[int]) -> List[UserRole]:
        """
        Obtiene múltiples UserRole por sus IDs.
        
        Args:
            user_role_ids: Lista de IDs de UserRole
            
        Returns:
            Lista de UserRole encontrados
        """
        return self.db.query(UserRole).filter(UserRole.user_role_id.in_(user_role_ids)).all() 