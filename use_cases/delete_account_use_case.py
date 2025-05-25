from fastapi import HTTPException
from utils.security import verify_session_token
from utils.response import create_response, session_token_invalid_response
from domain.repositories import UserRepository
import logging

logger = logging.getLogger(__name__)

class DeleteAccountUseCase:
    """
    Use case for deleting the account of the currently authenticated user.
    """
    def __init__(self, db):
        self.db = db
        self.user_repository = UserRepository(db)

    def execute(self, session_token: str):
        logger.info(f"Iniciando proceso de eliminación de cuenta para token: {session_token[:8]}...")
        # Verify the session token and get the user
        user = verify_session_token(session_token, self.db)
        if not user:
            logger.warning(f"Token de sesión inválido durante eliminación de cuenta: {session_token[:8]}...")
            return session_token_invalid_response()
        try:
            logger.debug(f"Eliminando cuenta para usuario ID: {user.user_id}, email: {user.email}")
            # Delete the user record (this will cascade to related records)
            self.db.delete(user)
            self.db.commit()
            logger.info(f"Cuenta eliminada exitosamente para usuario ID: {user.user_id}")
            return create_response("success", "Cuenta eliminada exitosamente")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error eliminando cuenta para token {session_token[:8]}...: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error eliminando cuenta: {str(e)}") 