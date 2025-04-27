from typing import Optional
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session
from models.models import Users, UserSessions
import random
import string

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def hash_password(password: str) -> str:
    """
    Hashea una contraseña utilizando el esquema configurado en CryptContext.

    Args:
        password (str): La contraseña en texto plano a hashear.

    Returns:
        str: La contraseña hasheada.
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica una contraseña en texto plano contra una contraseña hasheada.

    Args:
        plain_password (str): La contraseña en texto plano.
        hashed_password (str): La contraseña hasheada a comparar.

    Returns:
        bool: Verdadero si las contraseñas coinciden, falso en caso contrario.
    """
    return pwd_context.verify(plain_password, hashed_password)

def generate_verification_token(length: int=3) -> str:
    """
    Genera un token de verificación aleatorio.

    Args:
        length (int): La longitud del token. Por defecto es 3.

    Returns:
        str: Un token de verificación aleatorio compuesto por letras y dígitos.
    """
    characters = string.ascii_letters + string.digits  # Letras mayúsculas, minúsculas y dígitos
    return ''.join(random.choices(characters, k=length))

# Función auxiliar para verificar tokens de sesión
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