"""
Entidad de rol.
"""
from typing import Optional, List, TYPE_CHECKING
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from .permission import PermissionEntity

@dataclass
class Role:
    """
    Representa un rol en el dominio.
    
    Un rol define un conjunto de permisos que puede tener un usuario.
    """
    role_id: Optional[int] = None
    name: str = ""
    permissions: List['PermissionEntity'] = field(default_factory=list)
    
    def __post_init__(self):
        """Validaciones básicas después de la inicialización."""
        if not self.name or not self.name.strip():
            raise ValueError("El nombre del rol no puede estar vacío")
        self.name = self.name.strip()
    
    def add_permission(self, permission: 'PermissionEntity') -> None:
        """Agrega un permiso al rol."""
        if permission not in self.permissions:
            self.permissions.append(permission)
    
    def remove_permission(self, permission: 'PermissionEntity') -> None:
        """Remueve un permiso del rol."""
        if permission in self.permissions:
            self.permissions.remove(permission)
    
    def has_permission(self, permission_name: str) -> bool:
        """Verifica si el rol tiene un permiso específico."""
        return any(p.name == permission_name for p in self.permissions)
    
    def is_admin(self) -> bool:
        """Verifica si este es un rol de administrador."""
        return self.name.lower() in ['admin', 'administrator', 'administrador']
    
    def is_user(self) -> bool:
        """Verifica si este es un rol de usuario básico."""
        return self.name.lower() in ['user', 'usuario', 'basic']
    
    @classmethod
    def from_model(cls, model) -> 'Role':
        """Crea una entidad desde un modelo de SQLAlchemy."""
        if not model:
            return None
        
        # Importación local para evitar dependencias circulares
        from .permission import PermissionEntity
        
        permissions = []
        if hasattr(model, 'permissions') and model.permissions:
            permissions = [
                PermissionEntity.from_model(rp.permission) 
                for rp in model.permissions 
                if rp.permission
            ]
        
        return cls(
            role_id=model.role_id,
            name=model.name,
            permissions=permissions
        )
    
    def to_dict(self) -> dict:
        """Convierte la entidad a diccionario."""
        return {
            'role_id': self.role_id,
            'name': self.name,
            'permissions': [p.to_dict() for p in self.permissions]
        } 