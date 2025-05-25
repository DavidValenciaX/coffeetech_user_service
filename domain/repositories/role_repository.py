from typing import Optional, List
from sqlalchemy.orm import Session
from models.models import Roles
import logging

logger = logging.getLogger(__name__)

class RoleRepository:
    """Repositorio responsable únicamente de las operaciones de persistencia de roles."""
    
    def __init__(self, db: Session):
        self.db = db

    def find_all(self) -> List[Roles]:
        """
        Obtiene todos los roles.
        
        Returns:
            Lista de todos los roles
        """
        return self.db.query(Roles).all()
    
    def find_by_id(self, role_id: int) -> Optional[Roles]:
        """
        Obtiene un rol por su ID.
        
        Args:
            role_id: ID del rol
            
        Returns:
            Rol encontrado o None
        """
        return self.db.query(Roles).filter(Roles.role_id == role_id).first()
    
    def find_by_name(self, role_name: str) -> Optional[Roles]:
        """
        Obtiene un rol por su nombre.
        
        Args:
            role_name: Nombre del rol
            
        Returns:
            Rol encontrado o None
        """
        return self.db.query(Roles).filter(Roles.name == role_name).first()
    
    def create(self, role_data: dict) -> Roles:
        """
        Crea un nuevo rol.
        
        Args:
            role_data: Diccionario con los datos del rol
            
        Returns:
            Rol creado
            
        Raises:
            Exception: Si hay error al crear el rol
        """
        try:
            new_role = Roles(**role_data)
            self.db.add(new_role)
            self.db.commit()
            self.db.refresh(new_role)
            logger.info(f"Rol creado exitosamente: {role_data.get('name')}")
            return new_role
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error al crear rol: {str(e)}")
            raise
    
    def update(self, role: Roles, update_data: dict) -> Roles:
        """
        Actualiza un rol.
        
        Args:
            role: Rol a actualizar
            update_data: Diccionario con los datos a actualizar
            
        Returns:
            Rol actualizado
            
        Raises:
            Exception: Si hay error al actualizar el rol
        """
        try:
            for key, value in update_data.items():
                if hasattr(role, key):
                    setattr(role, key, value)
            
            self.db.commit()
            self.db.refresh(role)
            logger.info(f"Rol actualizado exitosamente: {role.name}")
            return role
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error al actualizar rol: {str(e)}")
            raise
    
    def delete(self, role: Roles) -> None:
        """
        Elimina un rol.
        
        Args:
            role: Rol a eliminar
            
        Raises:
            Exception: Si hay error al eliminar el rol
        """
        try:
            self.db.delete(role)
            self.db.commit()
            logger.info(f"Rol eliminado exitosamente: {role.name}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error al eliminar rol: {str(e)}")
            raise 