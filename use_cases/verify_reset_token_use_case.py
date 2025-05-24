from utils.response import create_response
from use_cases.forgot_password_use_case import reset_tokens
import datetime
import pytz
import logging

bogota_tz = pytz.timezone("America/Bogota")
logger = logging.getLogger(__name__)

def verify_reset_token(token: str):
    """
    Verifica si un token de restablecimiento de contraseña es válido y no ha expirado.
    
    Args:
        token (str): Token de restablecimiento de contraseña a verificar
        
    Returns:
        dict: Respuesta con el resultado de la verificación
    """
    logger.info("Iniciando la verificación del token: %s", token)
    logger.debug("Estado actual de reset_tokens: %s", reset_tokens)

    token_info = reset_tokens.get(token)

    if token_info:
        logger.info("Token encontrado: %s", token)

        current_time = datetime.datetime.now(bogota_tz)
        expires_at = token_info['expires_at']
        logger.debug("Hora actual: %s, Expira a: %s", current_time, expires_at)

        if current_time > expires_at:
            logger.info("El token ha expirado: %s", token)
            return create_response("error", "Token ha expirado")

        logger.info("Token válido, puede proceder a restablecer la contraseña.")
        return create_response("success", "Token válido. Puede proceder a restablecer la contraseña.")

    logger.warning("Token inválido o expirado: %s", token)
    return create_response("error", "Token inválido o expirado") 