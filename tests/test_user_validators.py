import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from domain.user_validator import UserValidator


class TestUserValidator:
    """Tests para la clase UserValidator."""
    
    def test_validate_name_valid(self):
        """Test que el nombre válido no retorna error."""
        result = UserValidator.validate_name("Juan Pérez")
        assert result is None
    
    def test_validate_name_empty(self):
        """Test que el nombre vacío retorna error."""
        result = UserValidator.validate_name("")
        assert result == "El nombre no puede estar vacío"
    
    def test_validate_name_whitespace(self):
        """Test que el nombre con solo espacios retorna error."""
        result = UserValidator.validate_name("   ")
        assert result == "El nombre no puede estar vacío"
    
    def test_validate_name_none(self):
        """Test que el nombre None retorna error."""
        result = UserValidator.validate_name(None)
        assert result == "El nombre no puede estar vacío"
    
    def test_validate_password_confirmation_match(self):
        """Test que contraseñas iguales no retorna error."""
        result = UserValidator.validate_password_confirmation("password123", "password123")
        assert result is None
    
    def test_validate_password_confirmation_mismatch(self):
        """Test que contraseñas diferentes retorna error."""
        result = UserValidator.validate_password_confirmation("password123", "password456")
        assert result == "Las contraseñas no coinciden"
    
    def test_validate_password_strength_valid(self):
        """Test que contraseña fuerte no retorna error."""
        result = UserValidator.validate_password_strength("MyPassword123!")
        assert result is None
    
    def test_validate_password_strength_too_short(self):
        """Test que contraseña corta retorna error."""
        result = UserValidator.validate_password_strength("Pass1!")
        assert result == "La contraseña debe tener al menos 8 caracteres"
    
    def test_validate_password_strength_no_uppercase(self):
        """Test que contraseña sin mayúscula retorna error."""
        result = UserValidator.validate_password_strength("mypassword123!")
        assert result == "La contraseña debe incluir al menos una letra mayúscula"
    
    def test_validate_password_strength_no_lowercase(self):
        """Test que contraseña sin minúscula retorna error."""
        result = UserValidator.validate_password_strength("MYPASSWORD123!")
        assert result == "La contraseña debe incluir al menos una letra minúscula"
    
    def test_validate_password_strength_no_number(self):
        """Test que contraseña sin número retorna error."""
        result = UserValidator.validate_password_strength("MyPassword!")
        assert result == "La contraseña debe incluir al menos un número"
    
    def test_validate_password_strength_no_special_char(self):
        """Test que contraseña sin carácter especial retorna error."""
        result = UserValidator.validate_password_strength("MyPassword123")
        assert result == "La contraseña debe incluir al menos un carácter especial"
    
    def test_validate_user_registration_valid(self):
        """Test que registro válido no retorna error."""
        result = UserValidator.validate_user_registration(
            "Juan Pérez",
            "MyPassword123!",
            "MyPassword123!"
        )
        assert result is None
    
    def test_validate_user_registration_invalid_name(self):
        """Test que registro con nombre inválido retorna error."""
        result = UserValidator.validate_user_registration(
            "",
            "MyPassword123!",
            "MyPassword123!"
        )
        assert result == "El nombre no puede estar vacío"
    
    def test_validate_user_registration_password_mismatch(self):
        """Test que registro con contraseñas diferentes retorna error."""
        result = UserValidator.validate_user_registration(
            "Juan Pérez",
            "MyPassword123!",
            "DifferentPassword123!"
        )
        assert result == "Las contraseñas no coinciden"
    
    def test_validate_user_registration_weak_password(self):
        """Test que registro con contraseña débil retorna error."""
        result = UserValidator.validate_user_registration(
            "Juan Pérez",
            "weak",
            "weak"
        )
        assert result == "La contraseña debe tener al menos 8 caracteres" 