from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from dataBase import get_db_session
from use_cases.login_use_case import LoginUseCase
from use_cases.register_user_use_case import RegisterUserUseCase
from use_cases.verify_email_use_case import VerifyEmailUseCase
from use_cases.forgot_password_use_case import ForgotPasswordUseCase
from use_cases.verify_reset_token_use_case import VerifyResetTokenUseCase
from use_cases.reset_password_use_case import ResetPasswordUseCase
from use_cases.change_password_use_case import ChangePasswordUseCase
from use_cases.logout_use_case import logout
from use_cases.delete_account_use_case import delete_account
from use_cases.update_profile_use_case import update_profile
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
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/register")
def register_user_endpoint(user: UserCreate, db: Session = Depends(get_db_session)):
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
    use_case = RegisterUserUseCase(db)
    return use_case.execute(user)

@router.post("/verify-email")
def verify_email_endpoint(request: VerifyTokenRequest, db: Session = Depends(get_db_session)):
    """
    Verifies a user's email address using a provided token.

    - **token**: The verification token sent to the user's email.

    Updates the user's state to "Verified" if the token is valid.
    Returns an error if the token is invalid or expired.
    """
    use_case = VerifyEmailUseCase(db)
    return use_case.execute(request.token)

@router.post("/forgot-password")
def forgot_password_endpoint(request: PasswordResetRequest, db: Session = Depends(get_db_session)):
    """
    Initiates the password reset process for a user.

    - **email**: The email address of the user requesting the password reset.

    Generates a password reset token, stores it temporarily, and sends it
    to the user's email address.
    Returns an error if the email is not found in the database.
    """
    use_case = ForgotPasswordUseCase(db)
    return use_case.execute(request)

@router.post("/verify-reset-token")
def verify_token(request: VerifyTokenRequest):
    """
    Verifies if a password reset token is valid and has not expired.

    - **token**: The password reset token to verify.

    Checks the token against the in-memory store.
    Returns a success message if the token is valid, allowing the user to proceed
    with password reset. Returns an error if the token is invalid or expired.
    """
    use_case = VerifyResetTokenUseCase()
    return use_case.execute(request.token)

@router.post("/reset-password")
def reset_password_endpoint(reset: PasswordReset, db: Session = Depends(get_db_session)):
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
    use_case = ResetPasswordUseCase(db)
    return use_case.execute(reset)

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
    use_case = LoginUseCase(db)
    return use_case.execute(request)

@router.put("/change-password")
def change_password_endpoint(change: PasswordChange, session_token: str, db: Session = Depends(get_db_session)):
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
    use_case = ChangePasswordUseCase(db)
    return use_case.execute(change, session_token)

@router.post("/logout")
def logout_endpoint(request: LogoutRequest, db: Session = Depends(get_db_session)):
    """
    Logs out a user by deleting their session token record.

    - **session_token**: The session token of the user to log out.

    Finds the session by the session token and deletes the corresponding
    `UserSessions` record from the database. Optionally clears the FCM token.
    Returns an error if the session token is invalid.
    """
    return logout(request, db)

@router.delete("/delete-account")
def delete_account_endpoint(session_token: str, db: Session = Depends(get_db_session)):
    """
    Deletes the account of the currently authenticated user.

    Requires a valid `session_token` provided as a query parameter or header.

    Finds the user by the session token and permanently deletes their record
    from the database.
    Returns an error if the session token is invalid.
    """
    return delete_account(session_token, db)

@router.post("/update-profile")
def update_profile_endpoint(profile: UpdateProfile, session_token: str, db: Session = Depends(get_db_session)):
    """
    Updates the profile information (currently only the name) for the authenticated user.

    Requires a valid `session_token` provided as a query parameter or header.

    - **new_name**: The new name for the user. Cannot be empty.

    Finds the user by the session token and updates their name.
    Returns an error if the session token is invalid or the new name is empty.
    """
    return update_profile(profile, session_token, db)
