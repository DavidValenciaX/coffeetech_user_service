import logging
from fastapi import HTTPException
from models.models import UserSessions
from utils.response import create_response, session_token_invalid_response

logger = logging.getLogger(__name__)

class LogoutUseCase:
    def __init__(self, db):
        self.db = db

    def execute(self, request):
        """
        Logs out a user by deleting their session token record.
        Args:
            request: LogoutRequest object containing the session_token
        Returns:
            Response object with success or error message
        """
        logger.info(f"Iniciando proceso de cierre de sesión para token: {request.session_token[:8]}...")
        session = self.db.query(UserSessions).filter(UserSessions.session_token == request.session_token).first()
        if not session:
            logger.warning(f"Token de sesión no encontrado: {request.session_token[:8]}...")
            return session_token_invalid_response()
        try:
            logger.debug(f"Eliminando sesión para usuario ID: {session.user_id}")
            self.db.delete(session)
            self.db.commit()
            logger.info(f"Cierre de sesión exitoso para usuario ID: {session.user_id}")
            return create_response("success", "Cierre de sesión exitoso")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error durante el cierre de sesión para el token {request.session_token[:8]}...: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error durante el cierre de sesión: {str(e)}") 