from fastapi import HTTPException
from utils.security import verify_session_token
from utils.response import create_response, session_token_invalid_response
from domain.repositories import UserRepository
from domain.validators import UserValidator
import logging

logger = logging.getLogger(__name__)

class UpdateProfileUseCase:
    def __init__(self, db):
        self.db = db
        self.user_repository = UserRepository(db)

    def execute(self, profile, session_token):
        """
        Updates the profile information (currently only the name) for the authenticated user.
        Args:
            profile: UpdateProfile object containing new_name
            session_token: The session token of the authenticated user
        Returns:
            Response object with success or error message
        """
        logger.info("Iniciando proceso de actualización de perfil")
        user = verify_session_token(session_token, self.db)
        if not user:
            logger.warning("Token de sesión inválido para actualización de perfil")
            return session_token_invalid_response()

        # Validar el nuevo nombre usando UserValidator
        name_error = UserValidator.validate_name(profile.new_name)
        if name_error:
            logger.warning(f"Intento de actualizar perfil con nombre inválido para el usuario: {user.email}")
            return create_response("error", name_error)

        try:
            old_name = user.name
            user.name = profile.new_name
            self.db.commit()
            logger.info(f"Perfil actualizado exitosamente para el usuario: {user.email}. Nombre anterior: {old_name}, Nuevo nombre: {profile.new_name}")
            return create_response("success", "Perfil actualizado exitosamente")
        except Exception as e:
            logger.error(f"Error al actualizar el perfil para el usuario {user.email}: {str(e)}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Error al actualizar el perfil: {str(e)}") 