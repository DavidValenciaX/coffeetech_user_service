"""
Entidad de usuario.
"""
from typing import Optional, List, TYPE_CHECKING
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from .user_state_entity import UserStateEntity
    from .user_role_entity import UserRoleEntity
    from .user_session_entity import UserSessionEntity
    from .user_device_entity import UserDeviceEntity

@dataclass
class UserEntity:
    """
    Representa un usuario en el dominio.
    
    Esta es la entidad central que encapsula toda la lógica de negocio
    relacionada con los usuarios.
    """
    user_id: Optional[int] = None
    name: str = ""
    email: str = ""
    password_hash: str = ""
    verification_token: Optional[str] = None
    user_state: Optional['UserStateEntity'] = None
    roles: List['UserRoleEntity'] = field(default_factory=list)
    sessions: List['UserSessionEntity'] = field(default_factory=list)
    devices: List['UserDeviceEntity'] = field(default_factory=list)
    
    def __post_init__(self):
        """Validaciones básicas después de la inicialización."""
        if not self.name or not self.name.strip():
            raise ValueError("El nombre del usuario no puede estar vacío")
        if not self.email or not self.email.strip():
            raise ValueError("El email del usuario no puede estar vacío")
        
        self.name = self.name.strip()
        self.email = self.email.strip().lower()
    
    def is_verified(self) -> bool:
        """Verifica si el usuario está verificado."""
        return self.user_state and self.user_state.is_verified()
    
    def is_unverified(self) -> bool:
        """Verifica si el usuario no está verificado."""
        return self.user_state and self.user_state.is_unverified()
    
    def is_suspended(self) -> bool:
        """Verifica si el usuario está suspendido."""
        return self.user_state and self.user_state.is_suspended()
    
    def has_role(self, role_name: str) -> bool:
        """Verifica si el usuario tiene un rol específico."""
        return any(ur.role and ur.role.name == role_name for ur in self.roles)
    
    def has_permission(self, permission_name: str) -> bool:
        """Verifica si el usuario tiene un permiso específico."""
        for user_role in self.roles:
            if user_role.role and user_role.role.has_permission(permission_name):
                return True
        return False
    
    def is_admin(self) -> bool:
        """Verifica si el usuario es administrador."""
        return any(ur.role and ur.role.is_admin() for ur in self.roles)
    
    def add_role(self, user_role: 'UserRoleEntity') -> None:
        """Agrega un rol al usuario."""
        if user_role not in self.roles:
            self.roles.append(user_role)
    
    def remove_role(self, role_name: str) -> None:
        """Remueve un rol del usuario."""
        self.roles = [ur for ur in self.roles if not (ur.role and ur.role.name == role_name)]
    
    def add_session(self, session: 'UserSessionEntity') -> None:
        """Agrega una sesión al usuario."""
        if session not in self.sessions:
            self.sessions.append(session)
    
    def remove_session(self, session_token: str) -> None:
        """Remueve una sesión del usuario."""
        self.sessions = [s for s in self.sessions if s.session_token != session_token]
    
    def add_device(self, device: 'UserDeviceEntity') -> None:
        """Agrega un dispositivo al usuario."""
        if device not in self.devices:
            self.devices.append(device)
    
    def remove_device(self, fcm_token: str) -> None:
        """Remueve un dispositivo del usuario."""
        self.devices = [d for d in self.devices if d.fcm_token != fcm_token]
    
    def get_active_sessions(self) -> List['UserSessionEntity']:
        """Obtiene las sesiones activas del usuario."""
        return [s for s in self.sessions if s.is_active()]
    
    def get_fcm_tokens(self) -> List[str]:
        """Obtiene todos los tokens FCM del usuario."""
        return [d.fcm_token for d in self.devices if d.fcm_token]
    
    @classmethod
    def from_model(cls, model) -> 'UserEntity':
        """Crea una entidad desde un modelo de SQLAlchemy."""
        if not model:
            return None
        
        # Importaciones locales para evitar dependencias circulares
        from .user_state_entity import UserStateEntity
        from .user_role_entity import UserRoleEntity
        from .user_session_entity import UserSessionEntity
        from .user_device_entity import UserDeviceEntity
        
        user_state = UserStateEntity.from_model(model.user_state) if hasattr(model, 'user_state') and model.user_state else None
        
        roles = []
        if hasattr(model, 'roles') and model.roles:
            roles = [UserRoleEntity.from_model(ur) for ur in model.roles]
        
        sessions = []
        if hasattr(model, 'sessions') and model.sessions:
            sessions = [UserSessionEntity.from_model(s) for s in model.sessions]
        
        devices = []
        if hasattr(model, 'devices') and model.devices:
            devices = [UserDeviceEntity.from_model(d) for d in model.devices]
        
        return cls(
            user_id=model.user_id,
            name=model.name,
            email=model.email,
            password_hash=model.password_hash,
            verification_token=model.verification_token,
            user_state=user_state,
            roles=roles,
            sessions=sessions,
            devices=devices
        )
    
    def to_dict(self) -> dict:
        """Convierte la entidad a diccionario."""
        return {
            'user_id': self.user_id,
            'name': self.name,
            'email': self.email,
            'verification_token': self.verification_token,
            'user_state': self.user_state.to_dict() if self.user_state else None,
            'roles': [r.to_dict() for r in self.roles],
            'sessions': [s.to_dict() for s in self.sessions],
            'devices': [d.to_dict() for d in self.devices]
        }
    
    def to_public_dict(self) -> dict:
        """Convierte la entidad a diccionario sin información sensible."""
        return {
            'user_id': self.user_id,
            'name': self.name,
            'email': self.email,
            'is_verified': self.is_verified(),
            'roles': [r.role.name for r in self.roles if r.role]
        } 