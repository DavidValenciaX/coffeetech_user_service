from fastapi import HTTPException
from sqlalchemy.orm import Session
from domain.user_validator import UserValidator
from domain.services import UserService, NotificationService
from utils.response import create_response
import logging

logger = logging.getLogger(__name__)


class RegisterUserUseCase:
    """
    Caso de uso responsable de orquestar el registro de usuarios.
    
    Este caso de uso coordina las diferentes operaciones necesarias para registrar
    un usuario, delegando responsabilidades específicas a sus respectivas clases.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.user_service = UserService(db)
        self.notification_service = NotificationService()
        self.user_validator = UserValidator()
    
    def execute(self, user_data) -> dict:
        """
        Ejecuta el caso de uso de registro de usuario.
        
        Args:
            user_data: UserCreate object con los datos de registro del usuario
            
        Returns:
            Response object con mensaje de éxito o error
            
        Raises:
            HTTPException: Si ocurre un error durante el proceso
        """
        try:
            # 1. Validar datos de entrada
            validation_error = self._validate_user_data(user_data)
            if validation_error:
                return create_response("error", validation_error)
            
            # 2. Verificar si el usuario ya existe
            existing_user = self.user_service.find_user_by_email(user_data.email)
            
            if existing_user:
                return self._handle_existing_user(existing_user, user_data)
            
            # 3. Crear nuevo usuario
            return self._create_new_user(user_data)
            
        except Exception as e:
            logger.error(f"Error en registro de usuario: {str(e)}")
            raise HTTPException(
                status_code=500, 
                detail=f"Error interno del servidor: {str(e)}"
            )
    
    def _validate_user_data(self, user_data) -> str:
        """
        Valida los datos del usuario.
        
        Args:
            user_data: Datos del usuario a validar
            
        Returns:
            Mensaje de error si hay problemas, None si todo está bien
        """
        return self.user_validator.validate_user_registration(
            user_data.name,
            user_data.password,
            user_data.passwordConfirmation
        )
    
    def _handle_existing_user(self, existing_user, user_data) -> dict:
        """
        Maneja el caso cuando el usuario ya existe.
        
        Args:
            existing_user: Entidad de usuario existente en la base de datos
            user_data: Nuevos datos del usuario
            
        Returns:
            Response object con el resultado de la operación
        """
        if existing_user.is_unverified():
            try:
                # Actualizar usuario no verificado
                updated_user = self.user_service.update_unverified_user(
                    existing_user,
                    user_data.name,
                    user_data.password
                )
                
                # Enviar nuevo email de verificación
                self.notification_service.send_verification_email(
                    user_data.email,
                    updated_user.verification_token
                )
                
                return create_response(
                    "success",
                    "Hemos enviado un correo electrónico para verificar tu cuenta nuevamente"
                )
                
            except Exception as e:
                logger.error(f"Error al actualizar usuario no verificado: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Error al actualizar usuario o enviar correo: {str(e)}"
                )
        else:
            return create_response("error", "El correo ya está registrado")
    
    def _create_new_user(self, user_data) -> dict:
        """
        Crea un nuevo usuario.
        
        Args:
            user_data: Datos del nuevo usuario
            
        Returns:
            Response object con el resultado de la operación
        """
        try:
            # Crear usuario
            new_user = self.user_service.create_user(
                user_data.name,
                user_data.email,
                user_data.password
            )
            
            # Enviar email de verificación
            self.notification_service.send_verification_email(
                user_data.email,
                new_user.verification_token
            )
            
            logger.info(f"Usuario registrado exitosamente: {user_data.email}")
            return create_response(
                "success",
                "Hemos enviado un correo electrónico para verificar tu cuenta"
            )
            
        except Exception as e:
            logger.error(f"Error al crear nuevo usuario: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error al registrar usuario o enviar correo: {str(e)}"
            ) 