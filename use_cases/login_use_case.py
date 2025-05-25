from fastapi import HTTPException
from models.models import Users, UserSessions, UserDevices
from utils.security import verify_password
from domain.services.token_service import generate_verification_token
from domain.services import email_service
from utils.response import create_response
from domain.user_state_repository import UserStateRepository, UserStateConstants
import logging

logger = logging.getLogger(__name__)

class LoginUseCase:
    def __init__(self, db):
        self.db = db
        self.user_state_repository = UserStateRepository(db)

    def _authenticate_user(self, request):
        """Authenticate user credentials."""
        user = self.db.query(Users).filter(Users.email == request.email).first()
        
        if not user or not verify_password(request.password, user.password_hash):
            return None
        
        return user

    def _check_user_verification_status(self, user):
        """Check if user is verified and return verification status."""
        verified_user_state = self.user_state_repository.get_user_state_by_name(UserStateConstants.VERIFIED)
        
        if not verified_user_state or user.user_state_id != verified_user_state.user_state_id:
            return False
        
        return True

    def _send_new_verification_token(self, user):
        """Generate and send new verification token to user."""
        try:
            new_verification_token = generate_verification_token(4)
            user.verification_token = new_verification_token
            self.db.commit()
            success = email_service.send_verification_email(user.email, new_verification_token)
            if not success:
                raise RuntimeError("Failed to send verification email")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error sending verification email to {user.email}: {str(e)}")
            raise HTTPException(
                status_code=500, 
                detail=f"Error al enviar el nuevo correo de verificación: {str(e)}"
            )

    def _create_user_session(self, user):
        """Create a new user session and return session token."""
        try:
            session_token = generate_verification_token(32)
            
            new_session = UserSessions(
                user_id=user.user_id,
                session_token=session_token
            )
            self.db.add(new_session)
            
            return session_token
        except Exception as e:
            logger.error(f"Error creating session for user {user.user_id}: {str(e)}")
            raise e

    def _register_user_device(self, user, fcm_token):
        """Register or update user device with FCM token."""
        if not fcm_token:
            return
        
        try:
            existing_device = self.db.query(UserDevices).filter(
                UserDevices.user_id == user.user_id,
                UserDevices.fcm_token == fcm_token
            ).first()
            
            if not existing_device:
                new_device = UserDevices(
                    user_id=user.user_id,
                    fcm_token=fcm_token
                )
                self.db.add(new_device)
                logger.info(f"Nuevo dispositivo registrado para usuario {user.user_id}")
            else:
                logger.info(f"Dispositivo ya registrado para usuario {user.user_id}")
        except Exception as e:
            logger.error(f"Error registering device for user {user.user_id}: {str(e)}")
            raise e

    def execute(self, request):
        """Main login orchestrator function."""
        # Step 1: Authenticate user credentials
        user = self._authenticate_user(request)
        if not user:
            return create_response("error", "Credenciales incorrectas")

        # Step 2: Check user verification status
        is_verified = self._check_user_verification_status(user)
        if not is_verified:
            self._send_new_verification_token(user)
            return create_response("error", "Debes verificar tu correo antes de iniciar sesión")

        # Step 3: Create user session and register device
        try:
            session_token = self._create_user_session(user)
            self._register_user_device(user, request.fcm_token)
            
            self.db.commit()
            
            logger.info(f"Session token generado para {user.email}: {session_token}")
            
            return create_response(
                "success", 
                "Inicio de sesión exitoso", 
                {"session_token": session_token, "name": user.name}
            )
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error durante el inicio de sesión para {request.email}: {str(e)}")
            raise HTTPException(
                status_code=500, 
                detail=f"Error durante el inicio de sesión: {str(e)}"
            )
