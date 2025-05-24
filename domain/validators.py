import re
from typing import Optional


class UserValidator:
    """Clase responsable de validar los datos de usuario."""
    
    @staticmethod
    def validate_name(name: str) -> Optional[str]:
        """
        Valida el nombre del usuario.
        
        Args:
            name: Nombre a validar
            
        Returns:
            None si es válido, mensaje de error si no es válido
        """
        if not name or not name.strip():
            return "El nombre no puede estar vacío"
        return None
    
    @staticmethod
    def validate_password_confirmation(password: str, password_confirmation: str) -> Optional[str]:
        """
        Valida que las contraseñas coincidan.
        
        Args:
            password: Contraseña
            password_confirmation: Confirmación de contraseña
            
        Returns:
            None si es válido, mensaje de error si no es válido
        """
        if password != password_confirmation:
            return "Las contraseñas no coinciden"
        return None
    
    @staticmethod
    def validate_password_strength(password: str) -> Optional[str]:
        """
        Valida la fortaleza de la contraseña.
        
        La contraseña debe tener al menos:
        - 8 caracteres
        - 1 letra mayúscula
        - 1 letra minúscula
        - 1 número
        - 1 carácter especial
        
        Args:
            password: Contraseña a validar
            
        Returns:
            None si es válido, mensaje de error si no es válido
        """
        if len(password) < 8:
            return "La contraseña debe tener al menos 8 caracteres"
        
        if not re.search(r'[A-Z]', password):
            return "La contraseña debe incluir al menos una letra mayúscula"
        
        if not re.search(r'[a-z]', password):
            return "La contraseña debe incluir al menos una letra minúscula"
        
        if not re.search(r'\d', password):
            return "La contraseña debe incluir al menos un número"
        
        if not re.search(r'[\W_]', password):
            return "La contraseña debe incluir al menos un carácter especial"
        
        return None
    
    @classmethod
    def validate_user_registration(cls, name: str, password: str, password_confirmation: str) -> Optional[str]:
        """
        Valida todos los campos necesarios para el registro de usuario.
        
        Args:
            name: Nombre del usuario
            password: Contraseña
            password_confirmation: Confirmación de contraseña
            
        Returns:
            None si es válido, mensaje de error si no es válido
        """
        # Validar nombre
        name_error = cls.validate_name(name)
        if name_error:
            return name_error
        
        # Validar confirmación de contraseña
        confirmation_error = cls.validate_password_confirmation(password, password_confirmation)
        if confirmation_error:
            return confirmation_error
        
        # Validar fortaleza de contraseña
        strength_error = cls.validate_password_strength(password)
        if strength_error:
            return strength_error
        
        return None 