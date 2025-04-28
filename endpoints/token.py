from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from utils.security import verify_session_token
from utils.response import create_response
from dataBase import get_db_session
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class TokenVerificationRequest(BaseModel):
    """
    Modelo de datos para la verificación de un token de sesión.
    
    **Atributos**:
    - **session_token**: Token de sesión a verificar.
    """
    session_token: str

class UserResponse(BaseModel):
    """
    Modelo de datos para la respuesta con información del usuario.
    
    **Atributos**:
    - **user_id**: ID único del usuario.
    - **name**: Nombre del usuario.
    - **email**: Correo electrónico del usuario.
    """
    user_id: int
    name: str
    email: str

@router.post("/session-token-verification", include_in_schema=False)
def verify_token(request: TokenVerificationRequest, db: Session = Depends(get_db_session)):
    """
    Verifica si un token de sesión es válido y devuelve información básica del usuario.
    
    **Parámetros**:
    - **request**: Objeto que contiene el token de sesión a verificar.
    - **db**: Sesión de base de datos, se obtiene automáticamente.
    
    **Respuestas**:
    - **200 OK**: Token válido, se devuelve información del usuario.
    - **401 Unauthorized**: Token inválido o no encontrado.
    """
    user = verify_session_token(request.session_token, db)
    if not user:
        logger.warning("Token de sesión inválido o usuario no encontrado")
        return create_response("error", "Token de sesión inválido o usuario no encontrado", status_code=401)
    
    return create_response("success", "Token de sesión válido", {
        "user": UserResponse(
            user_id=user.user_id,
            name=user.name,
            email=user.email
        )
    })
