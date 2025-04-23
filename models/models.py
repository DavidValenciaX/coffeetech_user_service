from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone

Base = declarative_base()

# Modelo para UserRoleFarm (relación entre usuarios, roles y fincas)
class UserRoleFarm(Base):
    """
    Relación entre usuarios, roles y fincas.

    Atributos:
    ----------
    user_role_farm_id : int
        Identificador único de la relación.
    role_id : int
        Identificador del rol (relación con Role).
    user_id : int
        Identificador del usuario (relación con User).
    farm_id : int
        Identificador de la finca (relación con Farm).
    status_id : int
        Estado actual de la relación.
    """
    __tablename__ = 'user_role_farm'
    __table_args__ = (
        UniqueConstraint('user_id', 'role_id', 'farm_id', name='unique_user_role_farm'),
    )

    user_role_farm_id = Column(Integer, primary_key=True)
    role_id = Column(Integer, ForeignKey('role.role_id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    farm_id = Column(Integer, nullable=False)
    status_id = Column(Integer, ForeignKey('status.status_id'), nullable=False)

    # Relaciones
    user = relationship('User', back_populates='user_roles_farms')
    role = relationship('Role', back_populates='user_roles_farms')
    status = relationship('Status')

# Modelo para Role
class Role(Base):
    """
    Representa un rol que un usuario puede tener.

    Atributos:
    ----------
    role_id : int
        Identificador único del rol.
    name : str
        Nombre del rol (único).
    """
    __tablename__ = 'role'

    role_id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)

    # Relación con RolePermission
    permissions = relationship("RolePermission", back_populates="role")
    user_roles_farms = relationship('UserRoleFarm', back_populates='role')

# Definición del modelo StatusType
class StatusType(Base):
    """
    Representa los tipos de estado de los registros.

    Atributos:
    ----------
    status_type_id : int
        Identificador único del tipo de estado.
    name : str
        Nombre del tipo de estado.
    """
    __tablename__ = 'status_type'

    status_type_id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)

    # Relación con Status
    statuses = relationship("Status", back_populates="status_type")

# Definición del modelo Status
class Status(Base):
    """
    Representa un estado de un registro (ejemplo: activo, inactivo).

    Atributos:
    ----------
    status_id : int
        Identificador único del estado.
    name : str
        Nombre del estado.
    status_type_id : int
        Relación con el tipo de estado.
    """
    __tablename__ = "status"

    status_id = Column(Integer, primary_key=True)
    name = Column(String(45), nullable=False)
    status_type_id = Column(Integer, ForeignKey("status_type.status_type_id"), nullable=False)

    # Relación con StatusType
    status_type = relationship("StatusType", back_populates="statuses")

    # Relación con User
    users = relationship("User", back_populates="status")
    
    # Relación con Notification
    notifications = relationship("Notification", back_populates="status")

# Definición del modelo User
class User(Base):
    """
    Representa un usuario en el sistema.

    Atributos:
    ----------
    user_id : int
        Identificador único del usuario.
    name : str
        Nombre del usuario.
    email : str
        Correo electrónico del usuario.
    password_hash : str
        Hash de la contraseña del usuario.
    verification_token : str
        Token de verificación del usuario.
    session_token : str
        Token de sesión del usuario.
    fcm_token : str
        Token de Firebase Cloud Messaging del usuario.
    status_id : int
        Relación con el estado del usuario.
    """
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(150), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    verification_token = Column(String(255), nullable=True)
    session_token = Column(String(255), nullable=True)
    fcm_token = Column(String(255), nullable=True)
    status_id = Column(Integer, ForeignKey("status.status_id"), nullable=False)

    # Relaciones
    status = relationship("Status", back_populates="users")
    user_roles_farms = relationship('UserRoleFarm', back_populates='user')
    notifications = relationship("Notification", foreign_keys="[Notification.user_id]", back_populates="user")

# Modelo para Permission
class Permission(Base):
    """
    Representa un permiso en el sistema.

    Atributos:
    ----------
    permission_id : int
        Identificador único del permiso.
    description : str
        Descripción del permiso.
    name : str
        Nombre del permiso.
    """

    __tablename__ = 'permission'

    permission_id = Column(Integer, primary_key=True)
    description = Column(String(200), nullable=False)
    name = Column(String(255), nullable=True, unique=True)

    # Relación con RolePermission
    roles = relationship("RolePermission", back_populates="permission")

# Modelo para RolePermission
class RolePermission(Base):
    """
    Representa la relación entre roles y permisos.

    Atributos:
    ----------
    role_id : int
        Identificador del rol.
    permission_id : int
        Identificador del permiso.
    """
    __tablename__ = 'role_permission'

    role_id = Column(Integer, ForeignKey('role.role_id'), primary_key=True, nullable=False)
    permission_id = Column(Integer, ForeignKey('permission.permission_id'), primary_key=True, nullable=False)

    # Relaciones con Role y Permission
    role = relationship("Role", back_populates="permissions")
    permission = relationship("Permission", back_populates="roles")

# Modelo para Invitation
class Invitation(Base):
    """
    Representa una invitación para un usuario.

    Atributos:
    ----------
    invitation_id : int
        Identificador único de la invitación.
    email : str
        Correo electrónico del invitado.
    suggested_role_id : int
        Identificador del rol sugerido (relación con Role).
    status_id : int
        Relación con el estado de la invitación.
    farm_id : int
        Relación con la finca a la que se invita.
    inviter_user_id : int
        Identificador del usuario que envía la invitación.
    date : datetime
        Fecha de creación de la invitación.
    """
    __tablename__ = 'invitation'

    invitation_id = Column(Integer, primary_key=True)
    email = Column(String(150), nullable=False)
    suggested_role_id = Column(Integer, ForeignKey('role.role_id'), nullable=False) # Add this line
    status_id = Column(Integer, ForeignKey('status.status_id'), nullable=False)
    farm_id = Column(Integer, nullable=False)
    inviter_user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    date = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)

    # Relaciones
    status = relationship("Status")
    inviter = relationship("User", foreign_keys=[inviter_user_id])
    notifications = relationship("Notification", back_populates="invitation")
    suggested_role = relationship("Role") # Add this relationship

# Modelo para NotificationType
class NotificationType(Base):
    """
    Representa el tipo de notificación.

    Atributos:
    ----------
    notification_type_id : int
        Identificador único del tipo de notificación.
    name : str
        Nombre del tipo de notificación.
    """
    __tablename__ = 'notification_type'

    notification_type_id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)

    # Relación con Notification
    notifications = relationship("Notification", back_populates="notification_type")

# Modelo para Notification
class Notification(Base):
    """
    Representa una notificación en el sistema.

    Atributos:
    ----------
    notifications_id : int
        Identificador único de la notificación.
    message : str
        Mensaje de la notificación.
    date : datetime
        Fecha de creación de la notificación.
    user_id : int
        Identificador del usuario que recibe la notificación.
    invitation_id : int
        Identificador de la invitación relacionada, si aplica.
    notification_type_id : int
        Tipo de notificación.
    farm_id : int
        Identificador de la finca relacionada, si aplica.
    status_id : int
        Relación con el estado de la notificación.
    """
    __tablename__ = 'notifications'

    notifications_id = Column(Integer, primary_key=True)
    message = Column(String(255), nullable=True)
    date = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    invitation_id = Column(Integer, ForeignKey('invitation.invitation_id'), nullable=True)
    notification_type_id = Column(Integer, ForeignKey('notification_type.notification_type_id'), nullable=True)
    farm_id = Column(Integer, nullable=True)
    status_id = Column(Integer, ForeignKey('status.status_id'), nullable=True)

    # Relaciones
    user = relationship("User", foreign_keys=[user_id], back_populates="notifications")
    invitation = relationship("Invitation", back_populates="notifications")
    notification_type = relationship("NotificationType", back_populates="notifications")
    
    # Agregar la relación con Status
    status = relationship("Status", back_populates="notifications")
