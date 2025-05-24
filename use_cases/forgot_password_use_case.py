from fastapi import HTTPException
from models.models import Users
from utils.security import generate_verification_token
from utils.email import send_email
from utils.response import create_response
import datetime
import pytz
import logging

bogota_tz = pytz.timezone("America/Bogota")
logger = logging.getLogger(__name__)

# Global dictionary to store reset tokens temporarily
reset_tokens = {}

def forgot_password(request, db):
    """
    Initiates the password reset process for a user.
    
    Args:
        request: PasswordResetRequest object containing the email
        db: Database session
        
    Returns:
        Response object with success or error message
    """
    global reset_tokens

    logger.info("Iniciando el proceso de restablecimiento de contraseña para el correo: %s", request.email)
    
    user = db.query(Users).filter(Users.email == request.email).first()
    
    if not user:
        logger.warning("Correo no encontrado: %s", request.email)
        return create_response("error", "Correo no encontrado")

    try:
        # Genera un token único para restablecer la contraseña
        reset_token = generate_verification_token(4)
        logger.info("Token de restablecimiento generado: %s", reset_token)

        # Configura el tiempo de expiración para 15 minutos en el futuro
        expiration_time = datetime.datetime.now(bogota_tz) + datetime.timedelta(minutes=15)
        logger.info("Tiempo de expiración del token establecido para: %s", expiration_time)

        # Almacenar el token en la base de datos
        user.verification_token = reset_token
        logger.info("Token de restablecimiento guardado en la base de datos para el usuario: %s", user.email)

        # Guardar el token y el tiempo de expiración en el diccionario global, sobrescribiendo el token existente si lo hay
        reset_tokens[reset_token] = {
            "expires_at": expiration_time,
            "email": request.email
        }
        logger.info("Token de restablecimiento almacenado globalmente para el correo: %s", request.email)

        # Guardar cambios en la base de datos
        db.commit()
        logger.info("Cambios guardados en la base de datos para el usuario: %s", user.email)

        # Envía un correo electrónico con el token de restablecimiento
        send_email(request.email, reset_token, 'reset')
        logger.info("Correo electrónico de restablecimiento enviado a: %s", request.email)

        return create_response("success", "Correo electrónico de restablecimiento de contraseña enviado")

    except Exception as e:
        logger.error("Error durante el proceso de restablecimiento de contraseña: %s", str(e))
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error sending password reset email: {str(e)}") 