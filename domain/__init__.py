"""
Dominio del servicio de usuarios.

Este módulo contiene las clases de dominio, validadores, repositorios y servicios
que encapsulan la lógica de negocio del sistema de usuarios.
"""

from .user_validator import UserValidator
from .user_repository import UserRepository
from .user_role_repository import UserRoleRepository
from .user_device_repository import UserDeviceRepository
from .services import NotificationService
from .services import EmailService, email_service
from .services.user_role_service import UserRoleService
from .services.user_verification_service import UserVerificationService
from .services.user_device_service import UserDeviceService

__all__ = [
    'UserValidator',
    'UserRepository',
    'UserRoleRepository',
    'UserDeviceRepository',
    'NotificationService',
    'EmailService',
    'email_service',
    'UserRoleService',
    'UserVerificationService',
    'UserDeviceService'
] 