from fastapi import HTTPException
from utils.security import verify_session_token
from utils.response import create_response, session_token_invalid_response
import logging

logger = logging.getLogger(__name__)

def update_profile(profile, session_token, db):
    """
    Updates the profile information (currently only the name) for the authenticated user.
    
    Args:
        profile: UpdateProfile object containing new_name
        session_token: The session token of the authenticated user
        db: Database session
        
    Returns:
        Response object with success or error message
    """
    logger.info("Iniciando proceso de actualización de perfil")
    
    # Verificar el token de sesión y obtener el usuario
    user = verify_session_token(session_token, db)
    if not user:
        logger.warning("Token de sesión inválido para actualización de perfil")
        return session_token_invalid_response()
    
    # Validación de que el nuevo nombre no sea vacío
    if not profile.new_name.strip():
        logger.warning(f"Intento de actualizar perfil con nombre vacío para el usuario: {user.email}")
        return create_response("error", "El nombre no puede estar vacío")

    try:
        # Solo actualizamos el nombre del usuario
        old_name = user.name
        user.name = profile.new_name
        db.commit()
        
        logger.info(f"Perfil actualizado exitosamente para el usuario: {user.email}. Nombre anterior: {old_name}, Nuevo nombre: {profile.new_name}")
        return create_response("success", "Perfil actualizado exitosamente")
        
    except Exception as e:
        logger.error(f"Error al actualizar el perfil para el usuario {user.email}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar el perfil: {str(e)}") 