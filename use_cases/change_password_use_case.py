from fastapi import HTTPException
from utils.security import verify_session_token, verify_password, hash_password
from utils.response import create_response, session_token_invalid_response
from domain.validators import UserValidator
import logging

logger = logging.getLogger(__name__)

def change_password(change, session_token, db):
    """
    Changes the password for an authenticated user.
    
    Args:
        change: PasswordChange object containing current_password and new_password
        session_token: The session token of the authenticated user
        db: Database session
        
    Returns:
        Response object with success or error message
    """
    logger.info("Iniciando proceso de cambio de contraseña")
    
    # Verificar el token de sesión y obtener el usuario
    user = verify_session_token(session_token, db)
    if not user:
        logger.warning("Token de sesión inválido para cambio de contraseña")
        return session_token_invalid_response()
    
    # Verificar la contraseña actual
    if not verify_password(change.current_password, user.password_hash):
        logger.warning(f"Contraseña actual incorrecta para el usuario: {user.email}")
        return create_response("error", "Credenciales incorrectas")

    # Validar que la nueva contraseña cumpla con los requisitos de seguridad
    password_error = UserValidator.validate_password_strength(change.new_password)
    if password_error:
        logger.warning(f"Nueva contraseña no cumple requisitos de seguridad para el usuario: {user.email}")
        return create_response("error", password_error)

    try:
        # Generar hash de la nueva contraseña
        new_password_hash = hash_password(change.new_password)
        logger.debug("Hash de la nueva contraseña generado")
        
        # Actualizar la contraseña del usuario
        user.password_hash = new_password_hash
        db.commit()
        
        logger.info(f"Contraseña cambiada exitosamente para el usuario: {user.email}")
        return create_response("success", "Cambio de contraseña exitoso")
        
    except Exception as e:
        logger.error(f"Error al cambiar la contraseña para el usuario {user.email}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al cambiar la contraseña: {str(e)}") 