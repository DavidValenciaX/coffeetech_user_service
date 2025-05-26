"""
Entidad de estado de usuario.
"""
from typing import Optional
from dataclasses import dataclass

@dataclass
class UserState:
    """
    Representa un estado de usuario en el dominio.
    
    Estados típicos: 'Verificado', 'No Verificado', 'Suspendido', etc.
    """
    user_state_id: Optional[int] = None
    name: str = ""
    
    def __post_init__(self):
        """Validaciones básicas después de la inicialización."""
        if not self.name or not self.name.strip():
            raise ValueError("El nombre del estado no puede estar vacío")
        self.name = self.name.strip()
    
    def is_verified(self) -> bool:
        """Verifica si este estado representa un usuario verificado."""
        return self.name.lower() in ['verificado', 'verified', 'activo', 'active']
    
    def is_unverified(self) -> bool:
        """Verifica si este estado representa un usuario no verificado."""
        return self.name.lower() in ['no verificado', 'unverified', 'pendiente', 'pending']
    
    def is_suspended(self) -> bool:
        """Verifica si este estado representa un usuario suspendido."""
        return self.name.lower() in ['suspendido', 'suspended', 'bloqueado', 'blocked']
    
    @classmethod
    def from_model(cls, model) -> 'UserState':
        """Crea una entidad desde un modelo de SQLAlchemy."""
        if not model:
            return None
        return cls(
            user_state_id=model.user_state_id,
            name=model.name
        )
    
    def to_dict(self) -> dict:
        """Convierte la entidad a diccionario."""
        return {
            'user_state_id': self.user_state_id,
            'name': self.name
        } 