from fastapi import HTTPException
from sqlalchemy.orm import Session
from domain.services.token_service import verify_session_token
from utils.security import verify_password, hash_password
from utils.response import create_response, session_token_invalid_response
from domain.validators import UserValidator
from domain.schemas import PasswordChange
from models.models import Users
import logging

logger = logging.getLogger(__name__)


class ChangePasswordUseCase:
    """
    Use case responsible for handling password change operations for authenticated users.
    
    This class implements the business logic for changing a user's password,
    including session validation, current password verification, new password
    validation, and password update operations.
    """
    
    def __init__(self, db: Session):
        """
        Initialize the use case with database session.
        
        Args:
            db: Database session for performing operations
        """
        self.db = db
    
    def _validate_session_token(self, session_token: str) -> Users:
        """
        Validate the session token and retrieve the authenticated user.
        
        Args:
            session_token: The session token to validate
            
        Returns:
            Users: The authenticated user object
            
        Raises:
            None: Returns None if token is invalid (handled by caller)
        """
        user = verify_session_token(session_token, self.db)
        if not user:
            logger.warning("Invalid session token provided for password change")
        return user
    
    def _verify_current_password(self, current_password: str, user: Users) -> bool:
        """
        Verify that the provided current password matches the user's stored password.
        
        Args:
            current_password: The current password provided by the user
            user: The user object containing the stored password hash
            
        Returns:
            bool: True if password matches, False otherwise
        """
        is_valid = verify_password(current_password, user.password_hash)
        if not is_valid:
            logger.warning(f"Incorrect current password provided for user: {user.email}")
        return is_valid
    
    def _validate_new_password(self, new_password: str) -> str:
        """
        Validate that the new password meets security requirements.
        
        Args:
            new_password: The new password to validate
            
        Returns:
            str: Error message if validation fails, None if password is valid
        """
        password_error = UserValidator.validate_password_strength(new_password)
        if password_error:
            logger.warning("New password does not meet security requirements")
        return password_error
    
    def _update_user_password(self, user: Users, new_password: str) -> None:
        """
        Update the user's password in the database.
        
        Args:
            user: The user object to update
            new_password: The new password to set
            
        Raises:
            Exception: If there's an error updating the password
        """
        try:
            new_password_hash = hash_password(new_password)
            logger.debug("New password hash generated successfully")
            
            user.password_hash = new_password_hash
            self.db.commit()
            
            logger.info(f"Password changed successfully for user: {user.email}")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating password for user {user.email}: {str(e)}")
            raise
    
    def execute(self, change: PasswordChange, session_token: str):
        """
        Execute the password change operation.
        
        This method orchestrates the entire password change process:
        1. Validates the session token
        2. Verifies the current password
        3. Validates the new password strength
        4. Updates the password in the database
        
        Args:
            change: PasswordChange object containing current and new passwords
            session_token: The session token of the authenticated user
            
        Returns:
            Response object with success or error message
            
        Raises:
            HTTPException: If there's a server error during the operation
        """
        logger.info("Starting password change process")
        
        # Step 1: Validate session token and get user
        user = self._validate_session_token(session_token)
        if not user:
            return session_token_invalid_response()
        
        # Step 2: Verify current password
        if not self._verify_current_password(change.current_password, user):
            return create_response("error", "Credenciales incorrectas")
        
        # Step 3: Validate new password strength
        password_error = self._validate_new_password(change.new_password)
        if password_error:
            return create_response("error", password_error)
        
        # Step 4: Update password
        try:
            self._update_user_password(user, change.new_password)
            return create_response("success", "Cambio de contraseña exitoso")
            
        except Exception as e:
            logger.error(f"Error during password change for user {user.email}: {str(e)}")
            raise HTTPException(
                status_code=500, 
                detail=f"Error al cambiar la contraseña: {str(e)}"
            )