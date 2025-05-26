"""
Entidad de dispositivo de usuario.
"""
from typing import Optional
from dataclasses import dataclass

@dataclass
class UserDeviceEntity:
    """
    Representa un dispositivo (token FCM) asociado a un usuario en el dominio.
    """
    user_device_id: Optional[int] = None
    user_id: Optional[int] = None
    fcm_token: str = ""
    
    def __post_init__(self):
        """Validaciones básicas después de la inicialización."""
        if not self.fcm_token or not self.fcm_token.strip():
            raise ValueError("El token FCM no puede estar vacío")
        self.fcm_token = self.fcm_token.strip()
    
    def is_valid_token(self) -> bool:
        """Verifica si el token FCM tiene un formato válido básico."""
        # Validación básica: debe tener al menos 140 caracteres (típico de FCM)
        return len(self.fcm_token) >= 140
    
    def belongs_to_user(self, user_id: int) -> bool:
        """Verifica si este dispositivo pertenece al usuario especificado."""
        return self.user_id == user_id
    
    @classmethod
    def from_model(cls, model) -> 'UserDeviceEntity':
        """Crea una entidad desde un modelo de SQLAlchemy."""
        if not model:
            return None
        return cls(
            user_device_id=model.user_device_id,
            user_id=model.user_id,
            fcm_token=model.fcm_token
        )
    
    def to_dict(self) -> dict:
        """Convierte la entidad a diccionario."""
        return {
            'user_device_id': self.user_device_id,
            'user_id': self.user_id,
            'fcm_token': self.fcm_token,
            'is_valid': self.is_valid_token()
        } 