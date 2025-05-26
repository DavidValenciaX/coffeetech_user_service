"""
Entidad de permiso.
"""
from typing import Optional
from dataclasses import dataclass

@dataclass
class PermissionEntity:
    """
    Representa un permiso en el dominio.
    
    Un permiso define una acción específica que puede realizar un usuario.
    """
    permission_id: Optional[int] = None
    name: str = ""
    description: str = ""
    
    def __post_init__(self):
        """Validaciones básicas después de la inicialización."""
        if not self.name or not self.name.strip():
            raise ValueError("El nombre del permiso no puede estar vacío")
        self.name = self.name.strip()
        self.description = self.description.strip() if self.description else ""
    
    def is_read_permission(self) -> bool:
        """Verifica si es un permiso de lectura."""
        return 'read' in self.name.lower() or 'ver' in self.name.lower()
    
    def is_write_permission(self) -> bool:
        """Verifica si es un permiso de escritura."""
        return any(word in self.name.lower() for word in ['write', 'create', 'update', 'delete', 'escribir', 'crear', 'actualizar', 'eliminar'])
    
    def is_admin_permission(self) -> bool:
        """Verifica si es un permiso administrativo."""
        return 'admin' in self.name.lower() or 'administrar' in self.name.lower()
    
    @classmethod
    def from_model(cls, model) -> 'PermissionEntity':
        """Crea una entidad desde un modelo de SQLAlchemy."""
        if not model:
            return None
        return cls(
            permission_id=model.permission_id,
            name=model.name,
            description=model.description
        )
    
    def to_dict(self) -> dict:
        """Convierte la entidad a diccionario."""
        return {
            'permission_id': self.permission_id,
            'name': self.name,
            'description': self.description
        } 