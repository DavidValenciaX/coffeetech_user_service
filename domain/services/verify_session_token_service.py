from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from models.models import Users, UserSessions

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