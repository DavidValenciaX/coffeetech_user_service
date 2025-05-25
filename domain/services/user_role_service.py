from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from domain.user_role_repository import UserRoleRepository
import logging

logger = logging.getLogger(__name__)

class UserRoleService:
    """Servicio de dominio para la gestión de roles de usuario."""
    
    def __init__(self, db: Session):
        self.db = db
        self.user_role_repository = UserRoleRepository(db)
    
    def get_user_role_ids(self, user_id: int) -> List[int]:
        """
        Obtiene los IDs de roles de un usuario.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Lista de user_role_ids
            
        Raises:
            SQLAlchemyError: Si hay error en la base de datos
        """
        try:
            user_roles = self.user_role_repository.get_by_user_id(user_id)
            return [ur.user_role_id for ur in user_roles]
        except SQLAlchemyError as e:
            logger.error(f"Error getting user role IDs for user {user_id}: {str(e)}")
            raise
    
    def create_user_role(self, user_id: int, role_name: str) -> int:
        """
        Crea una relación usuario-rol.
        
        Args:
            user_id: ID del usuario
            role_name: Nombre del rol
            
        Returns:
            ID del UserRole creado o existente
            
        Raises:
            ValueError: Si el rol no existe
            SQLAlchemyError: Si hay error en la base de datos
        """
        try:
            # Buscar el rol por nombre
            role = self.user_role_repository.get_role_by_name(role_name)
            if not role:
                raise ValueError(f"Rol '{role_name}' no encontrado")
            
            # Verificar si ya existe la relación
            existing_user_role = self.user_role_repository.get_by_user_and_role(user_id, role.role_id)
            if existing_user_role:
                return existing_user_role.user_role_id
            
            # Crear nueva relación
            user_role = self.user_role_repository.create(user_id, role.role_id)
            return user_role.user_role_id
        except ValueError:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Error creating user role: {str(e)}")
            raise
    
    def get_user_role_info(self, user_role_id: int) -> Dict[str, Any]:
        """
        Obtiene información de un UserRole por su ID.
        
        Args:
            user_role_id: ID del UserRole
            
        Returns:
            Diccionario con información del UserRole
            
        Raises:
            ValueError: Si el UserRole no existe
            SQLAlchemyError: Si hay error en la base de datos
        """
        try:
            user_role = self.user_role_repository.get_by_id(user_role_id)
            if not user_role:
                raise ValueError(f"UserRole con ID {user_role_id} no encontrado")
            
            role = self.user_role_repository.get_role_by_id(user_role.role_id)
            
            return {
                "user_role_id": user_role.user_role_id,
                "user_id": user_role.user_id,
                "role_id": user_role.role_id,
                "role_name": role.name if role else "Unknown"
            }
        except ValueError:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Error getting user role info: {str(e)}")
            raise
    
    def get_user_role_permissions(self, user_role_id: int) -> List[Dict[str, Any]]:
        """
        Obtiene permisos de un user_role_id.
        
        Args:
            user_role_id: ID del UserRole
            
        Returns:
            Lista de permisos
            
        Raises:
            ValueError: Si el UserRole o Role no existe
            SQLAlchemyError: Si hay error en la base de datos
        """
        try:
            user_role = self.user_role_repository.get_by_id(user_role_id)
            if not user_role:
                raise ValueError(f"UserRole con ID {user_role_id} no encontrado")
            
            role = self.user_role_repository.get_role_by_id(user_role.role_id)
            if not role:
                raise ValueError(f"Role con ID {user_role.role_id} no encontrado")
            
            return [
                {
                    "permission_id": perm.permission.permission_id,
                    "name": perm.permission.name,
                    "description": perm.permission.description
                } for perm in role.permissions
            ]
        except ValueError:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Error getting user role permissions: {str(e)}")
            raise
    
    def get_bulk_user_role_info(self, user_role_ids: List[int]) -> List[Dict[str, Any]]:
        """
        Obtiene información de múltiples UserRole.
        
        Args:
            user_role_ids: Lista de IDs de UserRole
            
        Returns:
            Lista de información de colaboradores
            
        Raises:
            SQLAlchemyError: Si hay error en la base de datos
        """
        try:
            user_roles = self.user_role_repository.get_multiple_by_ids(user_role_ids)
            collaborators = []
            
            for ur in user_roles:
                user = self.user_role_repository.get_user_by_id(ur.user_id)
                role = self.user_role_repository.get_role_by_id(ur.role_id)
                
                if user and role:
                    collaborators.append({
                        "user_role_id": ur.user_role_id,
                        "user_id": user.user_id,
                        "user_name": user.name,
                        "user_email": user.email,
                        "role_id": role.role_id,
                        "role_name": role.name
                    })
            
            return collaborators
        except SQLAlchemyError as e:
            logger.error(f"Error getting bulk user role info: {str(e)}")
            raise
    
    def get_role_name_by_id(self, role_id: int) -> str:
        """
        Obtiene el nombre de un rol por su ID.
        
        Args:
            role_id: ID del rol
            
        Returns:
            Nombre del rol
            
        Raises:
            ValueError: Si el rol no existe
            SQLAlchemyError: Si hay error en la base de datos
        """
        try:
            role = self.user_role_repository.get_role_by_id(role_id)
            if not role:
                raise ValueError(f"Rol con ID {role_id} no encontrado")
            
            return role.name
        except ValueError:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Error getting role name: {str(e)}")
            raise
    
    def update_user_role(self, user_role_id: int, new_role_id: int) -> str:
        """
        Actualiza el rol de un UserRole.
        
        Args:
            user_role_id: ID del UserRole a actualizar
            new_role_id: ID del nuevo rol
            
        Returns:
            Nombre del nuevo rol
            
        Raises:
            ValueError: Si el UserRole o el nuevo rol no existen
            SQLAlchemyError: Si hay error en la base de datos
        """
        try:
            # Verificar si el user_role existe
            user_role = self.user_role_repository.get_by_id(user_role_id)
            if not user_role:
                raise ValueError(f"UserRole con ID {user_role_id} no encontrado")
            
            # Verificar si el nuevo rol existe
            role = self.user_role_repository.get_role_by_id(new_role_id)
            if not role:
                raise ValueError(f"Rol con ID {new_role_id} no encontrado")
            
            # Actualizar el role_id
            self.user_role_repository.update_role(user_role, new_role_id)
            
            return role.name
        except ValueError:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Error updating user role: {str(e)}")
            raise
    
    def delete_user_role(self, user_role_id: int) -> None:
        """
        Elimina un UserRole.
        
        Args:
            user_role_id: ID del UserRole a eliminar
            
        Raises:
            ValueError: Si el UserRole no existe
            SQLAlchemyError: Si hay error en la base de datos
        """
        try:
            user_role = self.user_role_repository.get_by_id(user_role_id)
            if not user_role:
                raise ValueError(f"UserRole con ID {user_role_id} no encontrado")
            
            self.user_role_repository.delete(user_role)
        except ValueError:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Error deleting user role: {str(e)}")
            raise 