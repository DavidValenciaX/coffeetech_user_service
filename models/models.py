from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Modelo para UserState
class UserStates(Base):
    """
    Representa un estado de usuario (activo, verificado, etc).

    Atributos:
    ----------
    user_state_id : int
        Identificador único del estado de usuario.
    name : str
        Nombre del estado (único).
    """
    __tablename__ = 'user_states'

    user_state_id = Column(Integer, primary_key=True)
    name = Column(String(45), nullable=False, unique=True)

    # Relación con User
    users = relationship("Users", back_populates="user_state")

# Modelo para Roles
class Roles(Base):
    """
    Representa un rol que un usuario puede tener.

    Atributos:
    ----------
    role_id : int
        Identificador único del rol.
    name : str
        Nombre del rol (único).
    """
    __tablename__ = 'roles'

    role_id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)

    # Relación con RolePermission y UserRole
    permissions = relationship("RolePermission", back_populates="role")
    users = relationship("UserRole", back_populates="role")

# Definición del modelo Users
class Users(Base):
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
    user_state_id : int
        Relación con el estado del usuario.
    """
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(150), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    verification_token = Column(String(255), nullable=True, unique=True)
    user_state_id = Column(Integer, ForeignKey("user_states.user_state_id"), nullable=False)

    # Relaciones
    user_state = relationship("UserStates", back_populates="users")
    sessions = relationship("UserSessions", back_populates="user", cascade="all, delete-orphan")
    devices = relationship("UserDevices", back_populates="user", cascade="all, delete-orphan")
    roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")

# Modelo para UserSessions
class UserSessions(Base):
    """
    Representa una sesión de usuario.

    Atributos:
    ----------
    user_session_id : int
        Identificador único de la sesión.
    user_id : int
        Identificador del usuario dueño de la sesión.
    session_token : str
        Token único de sesión.
    """
    __tablename__ = "user_sessions"

    user_session_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    session_token = Column(String(255), nullable=False, unique=True)

    # Relación con User
    user = relationship("Users", back_populates="sessions")

# Modelo para UserDevices
class UserDevices(Base):
    """
    Representa un dispositivo de usuario.

    Atributos:
    ----------
    user_device_id : int
        Identificador único del dispositivo.
    user_id : int
        Identificador del usuario dueño del dispositivo.
    fcm_token : str
        Token de Firebase Cloud Messaging.
    """
    __tablename__ = "user_devices"

    user_device_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    fcm_token = Column(String(255), nullable=False, unique=True)

    # Relación con User
    user = relationship("Users", back_populates="devices")

# Modelo para Permissions
class Permissions(Base):
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
    __tablename__ = 'permissions'

    permission_id = Column(Integer, primary_key=True)
    description = Column(String(200), nullable=False)
    name = Column(String(255), nullable=False, unique=True)

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

    role_id = Column(Integer, ForeignKey('roles.role_id'), primary_key=True, nullable=False)
    permission_id = Column(Integer, ForeignKey('permissions.permission_id'), primary_key=True, nullable=False)

    # Relaciones con Role y Permission
    role = relationship("Roles", back_populates="permissions")
    permission = relationship("Permissions", back_populates="roles")

# Modelo para UserRole
class UserRole(Base):
    """
    Representa la asignación de un rol a un usuario.

    Atributos:
    ----------
    user_role_id : int
        Identificador único de la asignación.
    user_id : int
        Identificador del usuario.
    role_id : int
        Identificador del rol.
    """
    __tablename__ = 'user_role'

    user_role_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    role_id = Column(Integer, ForeignKey('roles.role_id'), nullable=False)

    # Relaciones con User y Role
    user = relationship("Users", back_populates="roles")
    role = relationship("Roles", back_populates="users")
