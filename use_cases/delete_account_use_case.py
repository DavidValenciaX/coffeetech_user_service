from fastapi import HTTPException
from utils.security import verify_session_token
from utils.response import create_response, session_token_invalid_response
import logging

logger = logging.getLogger(__name__)

def delete_account(session_token, db):
    """
    Deletes the account of the currently authenticated user.
    
    Args:
        session_token (str): The session token of the user to delete
        db: Database session
        
    Returns:
        Response object with success or error message
    """
    logger.info(f"Iniciando proceso de eliminación de cuenta para token: {session_token[:8]}...")
    
    # Verify the session token and get the user
    user = verify_session_token(session_token, db)
    if not user:
        logger.warning(f"Token de sesión inválido durante eliminación de cuenta: {session_token[:8]}...")
        return session_token_invalid_response()

    try:
        logger.debug(f"Eliminando cuenta para usuario ID: {user.user_id}, email: {user.email}")
        
        # Delete the user record (this will cascade to related records)
        db.delete(user)
        db.commit()
        
        logger.info(f"Cuenta eliminada exitosamente para usuario ID: {user.user_id}")
        return create_response("success", "Cuenta eliminada exitosamente")
    except Exception as e:
        db.rollback()
        logger.error(f"Error eliminando cuenta para token {session_token[:8]}...: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error eliminando cuenta: {str(e)}") 