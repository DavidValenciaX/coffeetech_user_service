import random
import string
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from models.models import Users, UserSessions
import logging

logger = logging.getLogger(__name__)


def generate_verification_token(length: int = 3) -> str:
    """
    Genera un token de verificación aleatorio.

    Args:
        length (int): La longitud del token. Por defecto es 3.

    Returns:
        str: Un token de verificación aleatorio compuesto por letras y dígitos.
    """
    characters = string.ascii_letters + string.digits  # Letras mayúsculas, minúsculas y dígitos
    return ''.join(random.choices(characters, k=length))


def verify_session_token(session_token: str, db: Session) -> Optional[Users]:
    """
    Verifica si un token de sesión es válido y devuelve el usuario correspondiente.

    Args:
        session_token (str): El token de sesión a verificar.
        db (Session): La sesión de base de datos.

    Returns:
        User | None: El objeto usuario correspondiente al token de sesión, o None si no se encuentra o no es válido.
    """
    stmt = (
        select(Users)
        .join(UserSessions)
        .where(UserSessions.session_token == session_token)
    )
    return db.execute(stmt).scalar_one_or_none() 