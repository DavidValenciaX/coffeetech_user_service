from fastapi import HTTPException
from models.models import Users
from utils.security import hash_password
from utils.response import create_response
from domain.validators import UserValidator
from use_cases.forgot_password_use_case import reset_tokens
import datetime
import pytz
import logging

bogota_tz = pytz.timezone("America/Bogota")
logger = logging.getLogger(__name__)

def reset_password(reset, db):
    """
    Resets the user's password using a valid reset token.
    
    Args:
        reset: PasswordReset object containing token, new_password, and confirm_password
        db: Database session
        
    Returns:
        Response object with success or error message
    """
    logger.info("Iniciando el proceso de restablecimiento de contraseña para el token: %s", reset.token)

    # Verificar que las contraseñas coincidan
    if reset.new_password != reset.confirm_password:
        logger.warning("Las contraseñas no coinciden para el token: %s", reset.token)
        return create_response("error", "Las contraseñas no coinciden")

    # Validar que la nueva contraseña cumpla con los requisitos de seguridad
    if not UserValidator.validate_password_strength(reset.new_password):
        return create_response("error", "La nueva contraseña debe tener al menos 8 caracteres, incluir una letra mayúscula, una letra minúscula, un número y un carácter especial")

    # Verificar el token en el diccionario en memoria
    token_info = reset_tokens.get(reset.token)

    if token_info:
        logger.info("Token encontrado en memoria: %s", reset.token)

        # Verificar si el token ha expirado
        current_time = datetime.datetime.now(bogota_tz)
        expires_at = token_info['expires_at']
        logger.debug("Hora actual: %s, Expira a: %s", current_time, expires_at)

        if current_time > expires_at:
            logger.info("El token ha expirado: %s", reset.token)
            del reset_tokens[reset.token]  # Eliminar token expirado
            return create_response("error", "El token ha expirado")

        # Obtener el usuario de la base de datos usando el token
        user = db.query(Users).filter(Users.verification_token == reset.token).first()
        if not user:
            logger.warning("Usuario no encontrado para el token: %s", reset.token)
            return create_response("error", "Usuario no encontrado")

        try:
            # Actualizar la contraseña del usuario
            new_password_hash = hash_password(reset.new_password)
            logger.debug("Hash de la nueva contraseña generado: %s", new_password_hash)

            user.password_hash = new_password_hash
            logger.info("Contraseña actualizada para el usuario: %s", user.email)

            # Limpiar el token después de usarlo
            user.verification_token = None

            # Confirmar los cambios en la base de datos
            db.commit()
            logger.info("Cambios confirmados en la base de datos para el usuario: %s", user.email)

            # Eliminar el token del diccionario después de usarlo
            del reset_tokens[reset.token]
            logger.info("Token eliminado del diccionario global: %s", reset.token)

            return create_response("success", "Contraseña restablecida exitosamente")
            
        except Exception as e:
            logger.error("Error al restablecer la contraseña: %s", str(e))
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error al restablecer la contraseña: {str(e)}")
    else:
        logger.warning("Token inválido o expirado: %s", reset.token)
        return create_response("error", "Token inválido o expirado") 