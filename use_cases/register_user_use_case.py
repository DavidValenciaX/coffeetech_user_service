from fastapi import HTTPException
from models.models import Users
from utils.security import hash_password, generate_verification_token
from utils.email import send_email
from utils.response import create_response
from utils.state import get_user_state
import re
import logging

logger = logging.getLogger(__name__)

def validate_password_strength(password: str) -> bool:
    """
    Validates if a password meets the strength requirements.
    
    The password must have at least:
    - 8 characters
    - 1 uppercase letter
    - 1 lowercase letter
    - 1 number
    - 1 special character
    """
    if (len(password) >= 8 and
        re.search(r'[A-Z]', password) and
        re.search(r'[a-z]', password) and
        re.search(r'\d', password) and
        re.search(r'[\W_]', password)):
        return True
    return False

def register_user(user_data, db):
    """
    Registers a new user in the system.
    
    Args:
        user_data: UserCreate object with user registration data
        db: Database session
        
    Returns:
        Response object with success or error message
    """
    # Validación del nombre (no puede estar vacío)
    if not user_data.name.strip():
        return create_response("error", "El nombre no puede estar vacío")
    
    # Validación de la contraseña
    if user_data.password != user_data.passwordConfirmation:
        return create_response("error", "Las contraseñas no coinciden")
    
    if not validate_password_strength(user_data.password):
        return create_response("error", "La contraseña debe tener al menos 8 caracteres, incluir una letra mayúscula, una letra minúscula, un número y un carácter especial")
    
    # Verificar si el usuario ya existe
    db_user = db.query(Users).filter(Users.email == user_data.email).first()
    user_registry_state = get_user_state(db, "No Verificado")
    
    if db_user:
        # Si el usuario está como "No Verificado", actualiza sus datos y reenvía el correo
        if db_user.user_state_id == user_registry_state.user_state_id:
            try:
                db_user.name = user_data.name
                db_user.password_hash = hash_password(user_data.password)
                verification_token = generate_verification_token(4)
                db_user.verification_token = verification_token
                db.commit()
                db.refresh(db_user)
                send_email(user_data.email, verification_token, 'verification')
                return create_response("success", "Hemos enviado un correo electrónico para verificar tu cuenta nuevamente")
            except Exception as e:
                db.rollback()
                logger.error(f"Error al actualizar usuario o enviar correo: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Error al actualizar usuario o enviar correo: {str(e)}")
        else:
            return create_response("error", "El correo ya está registrado")

    try:
        password_hash = hash_password(user_data.password)
        verification_token = generate_verification_token(4)

        # Usar get_user_state para obtener el estado "No Verificado"
        user_registry_state = get_user_state(db, "No Verificado")
        if not user_registry_state:
            return create_response("error", "No se encontró el estado 'No Verificado' para usuarios", status_code=400)

        # Crear el nuevo usuario con estado "No Verificado"
        new_user = Users(
            name=user_data.name,
            email=user_data.email,
            password_hash=password_hash,
            verification_token=verification_token,
            user_state_id=user_registry_state.user_state_id
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        send_email(user_data.email, verification_token, 'verification')

        logger.info(f"Usuario registrado exitosamente: {user_data.email}")
        return create_response("success", "Hemos enviado un correo electrónico para verificar tu cuenta")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error al registrar usuario: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al registrar usuario o enviar correo: {str(e)}") 