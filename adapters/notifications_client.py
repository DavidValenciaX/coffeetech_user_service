import os
import logging
import httpx

# Cargar variables de entorno
from dotenv import load_dotenv
load_dotenv(encoding='utf-8')

logger = logging.getLogger(__name__)

NOTIFICATIONS_SERVICE_URL = os.getenv("NOTIFICATIONS_SERVICE_URL", "http://localhost:8001")

def register_device_to_notifications_service(fcm_token, user_id=None):
    """
    Llama al servicio de notificaciones para registrar/obtener el dispositivo por FCM token.
    Si el dispositivo no existe, lo crea.
    """
    try:
        payload = {"fcm_token": fcm_token}
        if user_id:
            payload["user_id"] = user_id
        with httpx.Client(timeout=5.0) as client:
            response = client.post(f"{NOTIFICATIONS_SERVICE_URL}/register-device", json=payload)
            response.raise_for_status()
            return response.json().get("data")
    except Exception as e:
        logger.error(f"Error al comunicarse con el servicio de notificaciones: {str(e)}")
        return None