from sqlalchemy.orm import Session
from models.models import Users
from utils.state import get_user_state
from utils.response import create_response
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

def verify_email(token: str, db: Session):
    """
    Verifica el email de un usuario usando el token de verificación.
    
    Args:
        token (str): Token de verificación del usuario
        db (Session): Sesión de base de datos
        
    Returns:
        dict: Respuesta con el resultado de la verificación
        
    Raises:
        HTTPException: Si ocurre un error durante la verificación
    """
    
    # Buscar el usuario por el token de verificación
    user = db.query(Users).filter(Users.verification_token == token).first()
    
    if not user:
        logger.warning(f"Token de verificación inválido: {token}")
        return create_response("error", "Token inválido")
    
    try:
        # Obtener el estado "Verificado" usando la utilidad
        verified_user_state = get_user_state(db, "Verificado")
        if not verified_user_state:
            logger.error("No se encontró el estado 'Verificado' para usuarios")
            return create_response("error", "No se encontró el estado 'Verificado' para usuarios", status_code=400)

        # Actualizar el usuario: marcar como verificado y cambiar el status_id
        user.verification_token = None
        user.user_state_id = verified_user_state.user_state_id
        
        logger.info(f"Usuario verificado exitosamente: {user.email}")
        
        # Guardar los cambios en la base de datos
        db.commit()
        
        return create_response("success", "Correo electrónico verificado exitosamente")
    
    except Exception as e:
        logger.error(f"Error al verificar el correo para el usuario {user.email if user else 'desconocido'}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al verificar el correo: {str(e)}") 