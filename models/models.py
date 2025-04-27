from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

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
