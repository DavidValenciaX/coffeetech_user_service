from fastapi import HTTPException
from models.models import Users, UserSessions, UserDevices
from utils.security import verify_password, generate_verification_token
from utils.email import send_email
from utils.response import create_response
from utils.state import get_user_state
import logging

logger = logging.getLogger(__name__)

def login(request, db):
    user = db.query(Users).filter(Users.email == request.email).first()

    if not user or not verify_password(request.password, user.password_hash):
        return create_response("error", "Credenciales incorrectas")

    verified_user_state = get_user_state(db, "Verificado")
    if not verified_user_state or user.user_state_id != verified_user_state.user_state_id:
        new_verification_token = generate_verification_token(4)
        user.verification_token = new_verification_token

        try:
            db.commit()
            send_email(user.email, new_verification_token, 'verification')
            return create_response("error", "Debes verificar tu correo antes de iniciar sesión")
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error al enviar el nuevo correo de verificación: {str(e)}")

    try:
        session_token = generate_verification_token(32)
        
        # Create a new UserSession record
        new_session = UserSessions(
            user_id=user.user_id,
            session_token=session_token
        )
        db.add(new_session)

        # Register or update user device directly in the user_service database
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
            else:
                logger.info(f"Dispositivo ya registrado para usuario {user.user_id}")

        db.commit()

        logger.info(f"Session token generado para {user.email}: {session_token}")

        return create_response("success", "Inicio de sesión exitoso", {"session_token": session_token, "name": user.name})
    except Exception as e:
        db.rollback()
        logger.error(f"Error durante el inicio de sesión para {request.email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error durante el inicio de sesión: {str(e)}")
