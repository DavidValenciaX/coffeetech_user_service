"""
Entidad de sesión de usuario.
"""
from typing import Optional
from dataclasses import dataclass

@dataclass
class UserSession:
    """
    Representa una sesión de usuario en el dominio.
    """
    user_session_id: Optional[int] = None
    user_id: Optional[int] = None
    session_token: str = ""
    
    def __post_init__(self):
        """Validaciones básicas después de la inicialización."""
        if not self.session_token or not self.session_token.strip():
            raise ValueError("El token de sesión no puede estar vacío")
        self.session_token = self.session_token.strip()
    
    @classmethod
    def from_model(cls, model) -> 'UserSession':
        """Crea una entidad desde un modelo de SQLAlchemy."""
        if not model:
            return None
        
        return cls(
            user_session_id=model.user_session_id,
            user_id=model.user_id,
            session_token=model.session_token
        )
    
    def to_dict(self) -> dict:
        """Convierte la entidad a diccionario."""
        return {
            'user_session_id': self.user_session_id,
            'user_id': self.user_id,
            'session_token': self.session_token
        } 