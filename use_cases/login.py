from fastapi import HTTPException
from models.models import Users, UserSessions
from utils.security import verify_password, generate_verification_token
from utils.email import send_email
from utils.response import create_response
from utils.state import get_user_state
import logging
import requests

logger = logging.getLogger(__name__)

NOTIFICATIONS_SERVICE_URL = "http://localhost:8001"

def get_device_from_notification_service(fcm_token, user_id=None):
    """
    Llama al servicio de notificaciones para registrar/obtener el dispositivo por FCM token.
    Si el dispositivo no existe, lo crea.
    """
    try:
        payload = {"fcm_token": fcm_token}
        if user_id:
            payload["user_id"] = user_id
        response = requests.post(f"{NOTIFICATIONS_SERVICE_URL}/notifications-service/register-device", json=payload, timeout=5)
        response.raise_for_status()
        return response.json().get("data")
    except Exception as e:
        logger.error(f"Error al comunicarse con el servicio de notificaciones: {str(e)}")
        return None

def login_use_case(request, db):
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

        # Update or create UserDevice record for FCM token
        # Check if a device with this FCM token already exists for this user
        
        # get device from notification service
        device = get_device_from_notification_service(request.fcm_token, user.user_id)
        # Si no hay device, el servicio de notificaciones lo crea y lo retorna

        db.commit()

        # Agrega un log para asegurarte de que el token fue generado
        logger.info(f"Session token generado para {user.email}: {session_token}")

        return create_response("success", "Inicio de sesión exitoso", {"session_token": session_token, "name": user.name})
    except Exception as e:
        db.rollback()
        # Log the detailed error
        logger.error(f"Error durante el inicio de sesión para {request.email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error durante el inicio de sesión: {str(e)}")
