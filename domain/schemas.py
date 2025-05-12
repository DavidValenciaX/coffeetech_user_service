from pydantic import BaseModel, EmailStr
from typing import List

class UserRoleCreateRequest(BaseModel):
    user_id: int
    role_name: str

class BulkUserRoleInfoRequest(BaseModel):
    user_role_ids: List[int]

class TokenVerificationRequest(BaseModel):
    """
    Modelo de datos para la verificación de un token de sesión.
    """
    session_token: str

class UserResponse(BaseModel):
    """
    Modelo de datos para la respuesta con información del usuario.
    """
    user_id: int
    name: str
    email: str

class UserVerificationByEmailRequest(BaseModel):
    email: str

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    passwordConfirmation: str

class VerifyTokenRequest(BaseModel):
    token: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    token: str
    new_password: str
    confirm_password: str  

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    fcm_token: str

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

class LogoutRequest(BaseModel):
    session_token: str

class UpdateProfile(BaseModel):
    new_name: str
