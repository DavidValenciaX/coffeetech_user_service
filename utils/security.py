import argon2
import random
import string

# Create Argon2 password hasher with recommended settings
ph = argon2.PasswordHasher()

def hash_password(password: str) -> str:
    """
    Hashea una contraseña utilizando Argon2.

    Args:
        password (str): La contraseña en texto plano a hashear.

    Returns:
        str: La contraseña hasheada.
    """
    return ph.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica una contraseña en texto plano contra una contraseña hasheada.

    Args:
        plain_password (str): La contraseña en texto plano.
        hashed_password (str): La contraseña hasheada a comparar.

    Returns:
        bool: Verdadero si las contraseñas coinciden, falso en caso contrario.
    """
    try:
        ph.verify(hashed_password, plain_password)
        return True
    except argon2.exceptions.VerifyMismatchError:
        return False
    except argon2.exceptions.InvalidHash:
        return False

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

