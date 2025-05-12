from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from models.models import Users, UserSessions
from utils.security import verify_session_token
from utils.security import hash_password, generate_verification_token , verify_password
from utils.email import send_email
from utils.response import create_response, session_token_invalid_response
from dataBase import get_db_session
from utils.state import get_user_state
from use_cases.login_use_case import login
from domain.schemas import (
    UserCreate,
    VerifyTokenRequest,
    PasswordResetRequest,
    PasswordReset,
    LoginRequest,
    PasswordChange,
    LogoutRequest,
    UpdateProfile,
)
import datetime, re, logging, pytz

bogota_tz = pytz.timezone("America/Bogota")

logger = logging.getLogger(__name__)

router = APIRouter()

reset_tokens = {}

# Función auxiliar para validar la contraseña
def validate_password_strength(password: str) -> bool:
    # La contraseña debe tener al menos:
    # - 8 caracteres
    # - 1 letra mayúscula
    # - 1 letra minúscula
    # - 1 número
    # - 1 carácter especial
    if (len(password) >= 8 and
        re.search(r'[A-Z]', password) and
        re.search(r'[a-z]', password) and
        re.search(r'[0-9]', password) and
        re.search(r'[\W_]', password)):
        return True
    return False

# Modificación del endpoint de registro
@router.post("/register")
def register_user(user: UserCreate, db: Session = Depends(get_db_session)):
    """
    Registers a new user in the system.

    - **name**: The full name of the user.
    - **email**: The user's email address. Must be unique.
    - **password**: The user's password. Must meet strength requirements.
    - **passwordConfirmation**: Confirmation of the user's password. Must match the password.

    Sends a verification email upon successful registration.
    Returns an error if the email is already registered, passwords don't match,
    or the password doesn't meet strength requirements.
    """
    # Validación del nombre (no puede estar vacío)
    if not user.name.strip():
        return create_response("error", "El nombre no puede estar vacío")
    
    # Validación de la contraseña
    if user.password != user.passwordConfirmation:
        return create_response("error", "Las contraseñas no coinciden")
    
    if not validate_password_strength(user.password):
        return create_response("error", "La contraseña debe tener al menos 8 caracteres, incluir una letra mayúscula, una letra minúscula, un número y un carácter especial")
    
    db_user = db.query(Users).filter(Users.email == user.email).first()
    user_registry_state = get_user_state(db, "No Verificado")
    if db_user:
        # Si el usuario está como "No Verificado", actualiza sus datos y reenvía el correo
        if (db_user.user_state_id == user_registry_state.user_state_id):
            try:
                db_user.name = user.name
                db_user.password_hash = hash_password(user.password)
                verification_token = generate_verification_token(4)
                db_user.verification_token = verification_token
                db.commit()
                db.refresh(db_user)
                send_email(user.email, verification_token, 'verification')
                return create_response("success", "Hemos enviado un correo electrónico para verificar tu cuenta nuevamente")
            except Exception as e:
                db.rollback()
                raise HTTPException(status_code=500, detail=f"Error al actualizar usuario o enviar correo: {str(e)}")
        else:
            return create_response("error", "El correo ya está registrado")

    try:
        password_hash = hash_password(user.password)
        verification_token = generate_verification_token(4)

        # Usar get_user_state para obtener el estado "No Verificado"
        user_registry_state = get_user_state(db, "No Verificado")
        if not user_registry_state:
            return create_response("error", "No se encontró el estado 'No Verificado' para usuarios", status_code=400)

        # Crear el nuevo usuario con estado "No Verificado"
        new_user = Users(
            name=user.name,
            email=user.email,
            password_hash=password_hash,
            verification_token=verification_token,
            user_state_id=user_registry_state.user_state_id
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        send_email(user.email, verification_token, 'verification')

        return create_response("success", "Hemos enviado un correo electrónico para verificar tu cuenta")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al registrar usuario o enviar correo: {str(e)}")

@router.post("/verify-email") # Renamed from /verify
def verify_email(request: VerifyTokenRequest, db: Session = Depends(get_db_session)):
    """
    Verifies a user's email address using a provided token.

    - **token**: The verification token sent to the user's email.

    Updates the user's state to "Verified" if the token is valid.
    Returns an error if the token is invalid or expired.
    """
    user = db.query(Users).filter(Users.verification_token == request.token).first()
    
    if not user:
        return create_response("error", "Token inválido")
    
    try:
        # Usar get_user_state para obtener el estado "Verificado"
        verified_user_state = get_user_state(db, "Verificado")
        if not verified_user_state:
            return create_response("error", "No se encontró el estado 'Verificado' para usuarios", status_code=400)

        # Actualizar el usuario: marcar como verificado y cambiar el status_id
        user.verification_token = None
        user.user_state_id = verified_user_state.user_state_id
        
        # Guardar los cambios en la base de datos
        db.commit()
        
        return create_response("success", "Correo electrónico verificado exitosamente")
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al verificar el correo: {str(e)}")

@router.post("/forgot-password")
def forgot_password(request: PasswordResetRequest, db: Session = Depends(get_db_session)):
    """
    Initiates the password reset process for a user.

    - **email**: The email address of the user requesting the password reset.

    Generates a password reset token, stores it temporarily, and sends it
    to the user's email address.
    Returns an error if the email is not found in the database.
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


@router.post("/verify-reset-token") # Renamed from /verify-token
def verify_token(request: VerifyTokenRequest):
    """
    Verifies if a password reset token is valid and has not expired.

    - **token**: The password reset token to verify.

    Checks the token against the in-memory store.
    Returns a success message if the token is valid, allowing the user to proceed
    with password reset. Returns an error if the token is invalid or expired.
    """
    global reset_tokens

    logger.info("Iniciando la verificación del token: %s", request.token)
    logger.debug("Estado actual de reset_tokens: %s", reset_tokens)

    token_info = reset_tokens.get(request.token)

    if token_info:
        logger.info("Token encontrado: %s", request.token)

        current_time = datetime.datetime.now(bogota_tz)
        expires_at = token_info['expires_at']
        logger.debug("Hora actual: %s, Expira a: %s", current_time, expires_at)

        if current_time > expires_at:
            logger.info("El token ha expirado: %s", request.token)
            return create_response("error", "Token ha expirado")

        logger.info("Token válido, puede proceder a restablecer la contraseña.")
        return create_response("success", "Token válido. Puede proceder a restablecer la contraseña.")

    logger.warning("Token inválido o expirado: %s", request.token)
    return create_response("error", "Token inválido o expirado")

@router.post("/reset-password")
def reset_password(reset: PasswordReset, db: Session = Depends(get_db_session)):
    """
    Resets the user's password using a valid reset token.

    - **token**: The password reset token.
    - **new_password**: The new password for the user. Must meet strength requirements.
    - **confirm_password**: Confirmation of the new password. Must match `new_password`.

    Updates the user's password if the token is valid, not expired, passwords match,
    and the new password meets strength requirements. Invalidates the token after use.
    Returns an error if passwords don't match, the new password is weak,
    or the token is invalid/expired.
    """
    global reset_tokens

    logger.info("Iniciando el proceso de restablecimiento de contraseña para el token: %s", reset.token)

    # Verificar que las contraseñas coincidan
    if reset.new_password != reset.confirm_password:
        logger.warning("Las contraseñas no coinciden para el token: %s", reset.token)
        return create_response("error", "Las contraseñas no coinciden")

    # Validar que la nueva contraseña cumpla con los requisitos de seguridad
    if not validate_password_strength(reset.new_password):
        return create_response("error", "La nueva contraseña debe tener al menos 8 caracteres, incluir una letra mayúscula, una letra minúscula, un número y un carácter especial")

    # Verificar el token en el diccionario en memoria
    token_info = reset_tokens.get(reset.token)

    if token_info:
        logger.info("Token encontrado en memoria: %s", reset.token)

        # Verificar si el token ha expirado
        current_time = datetime.datetime.now(bogota_tz)
        expires_at = token_info['expires_at']
        logger.debug("Hora actual: %s, Expira a: %s", current_time, expires_at)

        if current_time > expires_at:
            logger.info("El token ha expirado: %s", reset.token)
            del reset_tokens[reset.token]  # Eliminar token expirado
            return create_response("error", "El token ha expirado")

        # Obtener el usuario de la base de datos usando el token
        user = db.query(Users).filter(Users.verification_token == reset.token).first()
        if not user:
            logger.warning("Usuario no encontrado para el token: %s", reset.token)
            return create_response("error", "Usuario no encontrado")

        try:
            # Actualizar la contraseña del usuario
            new_password_hash = hash_password(reset.new_password)
            logger.debug("Hash de la nueva contraseña generado: %s", new_password_hash)

            user.password_hash = new_password_hash
            logger.info("Contraseña actualizada para el usuario: %s", user.email)

            # Limpiar el token después de usarlo
            user.verification_token = None

            # Confirmar los cambios en la base de datos
            db.commit()
            logger.info("Cambios confirmados en la base de datos para el usuario: %s", user.email)

            # Eliminar el token del diccionario después de usarlo
            del reset_tokens[reset.token]
            logger.info("Token eliminado del diccionario global: %s", reset.token)

            return create_response("success", "Contraseña restablecida exitosamente")
        except Exception as e:
            logger.error("Error al restablecer la contraseña: %s", str(e))
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error al restablecer la contraseña: {str(e)}")
    else:
        logger.warning("Token inválido o expirado: %s", reset.token)
        return create_response("error", "Token inválido o expirado")

@router.post("/login")
def login_endpoint(request: LoginRequest, db: Session = Depends(get_db_session)):
    """
    Authenticates a user and provides a session token.

    - **email**: The user's email address.
    - **password**: The user's password.
    - **fcm_token**: The Firebase Cloud Messaging token for push notifications.

    Verifies the user's credentials and email verification status.
    If credentials are valid and the email is verified, generates a session token,
    stores the FCM token, creates a user session record, and returns the session token and user's name.
    If the email is not verified, resends the verification email.
    Returns an error for incorrect credentials or if email verification is required.
    """
    return login(request, db)

@router.put("/change-password")
def change_password(change: PasswordChange, session_token: str, db: Session = Depends(get_db_session)):
    """
    Allows an authenticated user to change their password.

    Requires a valid `session_token` provided as a query parameter or header.

    - **current_password**: The user's current password.
    - **new_password**: The desired new password. Must meet strength requirements.

    Verifies the `session_token` and the `current_password`.
    Updates the password if the current password is correct and the new password
    meets strength requirements.
    Returns an error if the session token is invalid, the current password is incorrect,
    or the new password is weak.
    """
    user = verify_session_token(session_token, db)
    if not user or not verify_password(change.current_password, user.password_hash):
        return create_response("error", "Credenciales incorrectas")

    # Validar que la nueva contraseña cumpla con los requisitos de seguridad
    if not validate_password_strength(change.new_password):
        return create_response("error", "La nueva contraseña debe tener al menos 8 caracteres, incluir una letra mayúscula, una letra minúscula, un número y un carácter especial")

    try:
        new_password_hash = hash_password(change.new_password)
        user.password_hash = new_password_hash
        db.commit()
        return create_response("success", "Cambio de contraseña exitoso")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al cambiar la contraseña: {str(e)}")

@router.post("/logout")
def logout(request: LogoutRequest, db: Session = Depends(get_db_session)):
    """
    Logs out a user by deleting their session token record.

    - **session_token**: The session token of the user to log out.

    Finds the session by the session token and deletes the corresponding
    `UserSessions` record from the database. Optionally clears the FCM token.
    Returns an error if the session token is invalid.
    """
    
    # Find the session record using the token
    session = db.query(UserSessions).filter(UserSessions.session_token == request.session_token).first()

    if not session:
        # Use the standard invalid token response
        return session_token_invalid_response() 
        
    try:
        # Delete the session record
        db.delete(session)
        db.commit()
        return create_response("success", "Cierre de sesión exitoso")
    except Exception as e:
        db.rollback()
        logger.error(f"Error durante el cierre de sesión para el token {request.session_token}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error durante el cierre de sesión: {str(e)}")

@router.delete("/delete-account")
def delete_account(session_token: str, db: Session = Depends(get_db_session)):
    """
    Deletes the account of the currently authenticated user.

    Requires a valid `session_token` provided as a query parameter or header.

    Finds the user by the session token and permanently deletes their record
    from the database.
    Returns an error if the session token is invalid.
    """
    user = verify_session_token(session_token, db)
    if not user:
        return session_token_invalid_response()

    try:
        db.delete(user)
        db.commit()
        return create_response("success", "Cuenta eliminada exitosa")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting account: {str(e)}")

@router.post("/update-profile")
def update_profile(profile: UpdateProfile, session_token: str, db: Session = Depends(get_db_session)):
    """
    Updates the profile information (currently only the name) for the authenticated user.

    Requires a valid `session_token` provided as a query parameter or header.

    - **new_name**: The new name for the user. Cannot be empty.

    Finds the user by the session token and updates their name.
    Returns an error if the session token is invalid or the new name is empty.
    """
    user = verify_session_token(session_token, db)
    if not user:
        return session_token_invalid_response()
    
    # Validación de que el nuevo nombre no sea vacío
    if not profile.new_name.strip():
        return create_response("error", "El nombre no puede estar vacío")

    try:
        # Solo actualizamos el nombre del usuario
        user.name = profile.new_name
        db.commit()
        return create_response("success", "Perfil actualizado exitosamente")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar el perfil: {str(e)}")
