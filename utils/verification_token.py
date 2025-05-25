import random
import string

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