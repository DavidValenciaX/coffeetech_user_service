"""
Entidad de asignación de rol a usuario.
"""
from typing import Optional, TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from .role import Role

@dataclass
class UserRole:
    """
    Representa la asignación de un rol a un usuario en el dominio.
    """
    user_role_id: Optional[int] = None
    user_id: Optional[int] = None
    role_id: Optional[int] = None
    role: Optional['Role'] = None
    
    def __post_init__(self):
        """Validaciones básicas después de la inicialización."""
        if not self.user_id and not self.role_id:
            raise ValueError("Se debe especificar al menos user_id y role_id")
    
    def is_admin_role(self) -> bool:
        """Verifica si este es un rol de administrador."""
        return self.role and self.role.is_admin()
    
    def is_user_role(self) -> bool:
        """Verifica si este es un rol de usuario básico."""
        return self.role and self.role.is_user()
    
    def has_permission(self, permission_name: str) -> bool:
        """Verifica si este rol tiene un permiso específico."""
        return self.role and self.role.has_permission(permission_name)
    
    @classmethod
    def from_model(cls, model) -> 'UserRole':
        """Crea una entidad desde un modelo de SQLAlchemy."""
        if not model:
            return None
        
        # Importación local para evitar dependencias circulares en runtime
        from .role import Role
        
        role = Role.from_model(model.role) if hasattr(model, 'role') and model.role else None
        
        return cls(
            user_role_id=model.user_role_id,
            user_id=model.user_id,
            role_id=model.role_id,
            role=role
        )
    
    def to_dict(self) -> dict:
        """Convierte la entidad a diccionario."""
        return {
            'user_role_id': self.user_role_id,
            'user_id': self.user_id,
            'role_id': self.role_id,
            'role': self.role.to_dict() if self.role else None
        } 