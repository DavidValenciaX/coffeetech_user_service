from sqlalchemy.orm import Session
from utils.response import create_response
from fastapi import HTTPException
from domain.repositories import UserRepository
from domain.repositories.user_state_repository import UserStateNotFoundError
from domain.services import NotificationService
import logging

logger = logging.getLogger(__name__)


class TokenNotFoundError(Exception):
    """Exception raised when verification token is not found."""
    pass


class VerifyEmailUseCase:
    """
    Use case for verifying user email addresses.
    
    This class handles the business logic for email verification,
    including token validation and user state updates.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
        self.notification_service = NotificationService()
    
    def execute(self, token: str) -> dict:
        """
        Execute the email verification process.
        
        Args:
            token: Verification token from the user
            
        Returns:
            dict: Response with verification result
            
        Raises:
            HTTPException: If verification fails
        """
        try:
            # Find user by verification token
            user = self.user_repository.find_by_verification_token(token)
            if not user:
                logger.warning(f"Token de verificación inválido: {token}")
                return create_response("error", "Token inválido")
            
            # Verify the user's email
            self.user_repository.verify_user_email(user)
            
            # Optionally send welcome email
            try:
                self.notification_service.send_welcome_email(user.email)
            except Exception as e:
                # Log but don't fail the verification if welcome email fails
                logger.warning(f"No se pudo enviar email de bienvenida a {user.email}: {str(e)}")
            
            return create_response("success", "Correo electrónico verificado exitosamente")
            
        except UserStateNotFoundError as e:
            logger.error(str(e))
            return create_response("error", str(e), status_code=400)
            
        except Exception as e:
            logger.error(f"Error inesperado al verificar el correo: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error al verificar el correo: {str(e)}")