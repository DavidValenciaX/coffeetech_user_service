from fastapi import HTTPException
from models.models import Users, UserSessions, UserDevices
from utils.response import create_response
import logging

logger = logging.getLogger(__name__)

class LoginUseCase:
    def __init__(self, password_verifier, token_generator, email_sender, state_service):
        self.password_verifier = password_verifier
        self.token_generator = token_generator
        self.email_sender = email_sender
        self.state_service = state_service
    
    def execute(self, request, db):
        user = db.query(Users).filter(Users.email == request.email).first()

        if not user or not self.password_verifier.verify(request.password, user.password_hash):
            return create_response("error", "Credenciales incorrectas")

        verified_user_state = self.state_service.get_user_state(db, "Verificado")
        if not verified_user_state or user.user_state_id != verified_user_state.user_state_id:
            new_verification_token = self.token_generator.generate(4)
            user.verification_token = new_verification_token

            try:
                db.commit()
                self.email_sender.send(user.email, new_verification_token, 'verification')
                return create_response("error", "Debes verificar tu correo antes de iniciar sesión")
            except Exception as e:
                db.rollback()
                raise HTTPException(status_code=500, detail=f"Error al enviar el nuevo correo de verificación: {str(e)}")

        try:
            session_token = self.token_generator.generate(32)
            
            # Create a new UserSession record
            new_session = UserSessions(
                user_id=user.user_id,
                session_token=session_token
            )
            db.add(new_session)

            # Register or update user device
            if request.fcm_token:
                existing_device = db.query(UserDevices).filter(
                    UserDevices.user_id == user.user_id,
                    UserDevices.fcm_token == request.fcm_token
                ).first()
                
                if not existing_device:
                    new_device = UserDevices(
                        user_id=user.user_id,
                        fcm_token=request.fcm_token
                    )
                    db.add(new_device)
                    logger.info(f"Nuevo dispositivo registrado para usuario {user.user_id}")

            db.commit()
            logger.info(f"Session token generado para {user.email}: {session_token}")

            return create_response("success", "Inicio de sesión exitoso", {"session_token": session_token, "name": user.name})
        except Exception as e:
            db.rollback()
            logger.error(f"Error durante el inicio de sesión para {request.email}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error durante el inicio de sesión: {str(e)}")

# Factory function for easier usage
def create_login_use_case():
    from utils.security import verify_password, generate_verification_token
    from utils.email import send_email
    from utils.state import get_user_state
    
    class PasswordVerifier:
        def verify(self, password, hash): return verify_password(password, hash)
    
    class TokenGenerator:
        def generate(self, length): return generate_verification_token(length)
    
    class EmailSender:
        def send(self, email, token, type): return send_email(email, token, type)
    
    class StateService:
        def get_user_state(self, db, state): return get_user_state(db, state)
    
    return LoginUseCase(
        PasswordVerifier(),
        TokenGenerator(),
        EmailSender(),
        StateService()
    ) 