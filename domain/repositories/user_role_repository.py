from typing import Optional, List
from sqlalchemy.orm import Session
from models.models import UserRole
import logging

logger = logging.getLogger(__name__)

class UserRoleRepository:
    """Repositorio responsable únicamente de las operaciones de persistencia de UserRole."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def find_by_user_id(self, user_id: int) -> List[UserRole]:
        """
        Obtiene todos los UserRole de un usuario.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Lista de UserRole del usuario
        """
        return self.db.query(UserRole).filter(UserRole.user_id == user_id).all()
    
    def find_by_id(self, user_role_id: int) -> Optional[UserRole]:
        """
        Obtiene un UserRole por su ID.
        
        Args:
            user_role_id: ID del UserRole
            
        Returns:
            UserRole encontrado o None
        """
        return self.db.query(UserRole).filter(UserRole.user_role_id == user_role_id).first()
    
    def find_by_user_and_role(self, user_id: int, role_id: int) -> Optional[UserRole]:
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
    
    def find_multiple_by_ids(self, user_role_ids: List[int]) -> List[UserRole]:
        """
        Obtiene múltiples UserRole por sus IDs.
        
        Args:
            user_role_ids: Lista de IDs de UserRole
            
        Returns:
            Lista de UserRole encontrados
        """
        return self.db.query(UserRole).filter(UserRole.user_role_id.in_(user_role_ids)).all()
    
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
    
    def update(self, user_role: UserRole, update_data: dict) -> UserRole:
        """
        Actualiza un UserRole.
        
        Args:
            user_role: UserRole a actualizar
            update_data: Diccionario con los datos a actualizar
            
        Returns:
            UserRole actualizado
            
        Raises:
            Exception: Si hay error al actualizar el UserRole
        """
        try:
            for key, value in update_data.items():
                if hasattr(user_role, key):
                    setattr(user_role, key, value)
            
            self.db.commit()
            self.db.refresh(user_role)
            logger.info(f"UserRole actualizado: user_role_id={user_role.user_role_id}")
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