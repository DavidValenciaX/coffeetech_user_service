import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

import pytest
from unittest.mock import patch
from sqlalchemy.exc import SQLAlchemyError

from domain.services.user_verification_service import UserVerificationService
from domain.services.user_service import UserService
from domain.entities.user import User
from models.models import Users
from tests.mockdb import MockDB


class TestUserVerificationService:
    """Tests para la clase UserVerificationService."""
    
    def setup_method(self):
        """Configuración inicial para cada test."""
        self.mock_db = MockDB()
        self.verification_service = UserVerificationService(self.mock_db)
        
        # Mock user data
        self.sample_user = Users(
            user_id=1,
            name="Test User",
            email="test@example.com",
            password_hash="hashed_password",
            verification_token="verification_token_123",
            user_state_id=1
        )
        
        self.sample_user_entity = User(
            user_id=1,
            name="Test User",
            email="test@example.com",
            password_hash="hashed_password",
            verification_token="verification_token_123"
        )

    @patch('domain.services.user_verification_service.verify_session_token')
    def test_verify_session_token_success(self, mock_verify_session_token):
        """Test que verifica un token de sesión válido exitosamente."""
        # Arrange
        session_token = "valid_session_token_123"
        mock_verify_session_token.return_value = self.sample_user
        
        # Act
        result = self.verification_service.verify_session_token(session_token)
        
        # Assert
        assert result == self.sample_user
        mock_verify_session_token.assert_called_once_with(session_token, self.mock_db)

    @patch('domain.services.user_verification_service.verify_session_token')
    def test_verify_session_token_invalid_token(self, mock_verify_session_token):
        """Test que maneja el caso de token de sesión inválido."""
        # Arrange
        session_token = "invalid_session_token"
        mock_verify_session_token.return_value = None
        
        # Act & Assert
        with pytest.raises(ValueError, match="Token de sesión inválido o usuario no encontrado"):
            self.verification_service.verify_session_token(session_token)
        
        mock_verify_session_token.assert_called_once_with(session_token, self.mock_db)

    @patch('domain.services.user_verification_service.verify_session_token')
    @patch('domain.services.user_verification_service.logger')
    def test_verify_session_token_database_error(self, mock_logger, mock_verify_session_token):
        """Test que maneja errores de base de datos en verificación de token de sesión."""
        # Arrange
        session_token = "session_token_123"
        db_error = SQLAlchemyError("Database connection error")
        mock_verify_session_token.side_effect = db_error
        
        # Act & Assert
        with pytest.raises(SQLAlchemyError):
            self.verification_service.verify_session_token(session_token)
        
        mock_logger.error.assert_called_once_with(f"Error verifying session token: {str(db_error)}")

    @patch.object(UserService, 'find_user_by_email')
    def test_verify_user_by_email_user_exists(self, mock_find_user):
        """Test que verifica usuario existente por email."""
        # Arrange
        email = "test@example.com"
        mock_find_user.return_value = self.sample_user_entity
        
        # Act
        result = self.verification_service.verify_user_by_email(email)
        
        # Assert
        expected_result = {
            "user_id": 1,
            "name": "Test User",
            "email": "test@example.com"
        }
        assert result == expected_result
        mock_find_user.assert_called_once_with(email)

    @patch.object(UserService, 'find_user_by_email')
    def test_verify_user_by_email_user_not_exists(self, mock_find_user):
        """Test que maneja el caso cuando el usuario no existe."""
        # Arrange
        email = "nonexistent@example.com"
        mock_find_user.return_value = None
        
        # Act
        result = self.verification_service.verify_user_by_email(email)
        
        # Assert
        assert result is None
        mock_find_user.assert_called_once_with(email)

    @patch.object(UserService, 'find_user_by_email')
    @patch('domain.services.user_verification_service.logger')
    def test_verify_user_by_email_database_error(self, mock_logger, mock_find_user):
        """Test que maneja errores de base de datos en verificación por email."""
        # Arrange
        email = "test@example.com"
        db_error = SQLAlchemyError("Database connection error")
        mock_find_user.side_effect = db_error
        
        # Act & Assert
        with pytest.raises(SQLAlchemyError):
            self.verification_service.verify_user_by_email(email)
        
        mock_logger.error.assert_called_once_with(f"Error verifying user by email: {str(db_error)}")

    @patch.object(UserService, 'get_user_info')
    def test_get_user_by_id_user_exists(self, mock_get_user_info):
        """Test que obtiene información de usuario existente por ID."""
        # Arrange
        user_id = 1
        expected_user_info = {
            "user_id": 1,
            "name": "Test User",
            "email": "test@example.com",
            "user_state_id": 1,
            "is_verified": True,
            "is_suspended": False
        }
        mock_get_user_info.return_value = expected_user_info
        
        # Act
        result = self.verification_service.get_user_by_id(user_id)
        
        # Assert
        assert result == expected_user_info
        mock_get_user_info.assert_called_once_with(user_id)

    @patch.object(UserService, 'get_user_info')
    def test_get_user_by_id_user_not_exists(self, mock_get_user_info):
        """Test que maneja el caso cuando el usuario no existe por ID."""
        # Arrange
        user_id = 999
        mock_get_user_info.return_value = None
        
        # Act
        result = self.verification_service.get_user_by_id(user_id)
        
        # Assert
        assert result is None
        mock_get_user_info.assert_called_once_with(user_id)

    @patch.object(UserService, 'get_user_info')
    @patch('domain.services.user_verification_service.logger')
    def test_get_user_by_id_database_error(self, mock_logger, mock_get_user_info):
        """Test que maneja errores de base de datos en obtención de usuario por ID."""
        # Arrange
        user_id = 1
        db_error = SQLAlchemyError("Database connection error")
        mock_get_user_info.side_effect = db_error
        
        # Act & Assert
        with pytest.raises(SQLAlchemyError):
            self.verification_service.get_user_by_id(user_id)
        
        mock_logger.error.assert_called_once_with(f"Error getting user by ID: {str(db_error)}")

    def test_user_verification_service_initialization(self):
        """Test que verifica la correcta inicialización del servicio."""
        # Assert
        assert self.verification_service.db == self.mock_db
        assert isinstance(self.verification_service.user_service, UserService)
        assert self.verification_service.user_service.db == self.mock_db

    @patch.object(UserService, 'find_user_by_email')
    def test_verify_user_by_email_user_with_missing_attributes(self, mock_find_user):
        """Test que maneja usuarios con atributos faltantes."""
        # Arrange
        email = "test@example.com"
        incomplete_user = User(
            user_id=1,
            name="Test User",
            email="test@example.com"
            # Missing other attributes
        )
        mock_find_user.return_value = incomplete_user
        
        # Act
        result = self.verification_service.verify_user_by_email(email)
        
        # Assert
        expected_result = {
            "user_id": 1,
            "name": "Test User", 
            "email": "test@example.com"
        }
        assert result == expected_result

    @patch('domain.services.user_verification_service.verify_session_token')
    def test_verify_session_token_empty_token(self, mock_verify_session_token):
        """Test que maneja token de sesión vacío."""
        # Arrange
        session_token = ""
        mock_verify_session_token.return_value = None
        
        # Act & Assert
        with pytest.raises(ValueError, match="Token de sesión inválido o usuario no encontrado"):
            self.verification_service.verify_session_token(session_token)

    @patch('domain.services.user_verification_service.verify_session_token')
    def test_verify_session_token_none_token(self, mock_verify_session_token):
        """Test que maneja token de sesión None."""
        # Arrange
        session_token = None
        mock_verify_session_token.return_value = None
        
        # Act & Assert
        with pytest.raises(ValueError, match="Token de sesión inválido o usuario no encontrado"):
            self.verification_service.verify_session_token(session_token)

    @patch.object(UserService, 'find_user_by_email')
    def test_verify_user_by_email_empty_email(self, mock_find_user):
        """Test que maneja email vacío."""
        # Arrange
        email = ""
        mock_find_user.return_value = None
        
        # Act
        result = self.verification_service.verify_user_by_email(email)
        
        # Assert
        assert result is None
        mock_find_user.assert_called_once_with(email)

    @patch.object(UserService, 'get_user_info')
    def test_get_user_by_id_zero_user_id(self, mock_get_user_info):
        """Test que maneja ID de usuario cero."""
        # Arrange
        user_id = 0
        mock_get_user_info.return_value = None
        
        # Act
        result = self.verification_service.get_user_by_id(user_id)
        
        # Assert
        assert result is None
        mock_get_user_info.assert_called_once_with(user_id)

    @patch.object(UserService, 'get_user_info')
    def test_get_user_by_id_negative_user_id(self, mock_get_user_info):
        """Test que maneja ID de usuario negativo."""
        # Arrange
        user_id = -1
        mock_get_user_info.return_value = None
        
        # Act
        result = self.verification_service.get_user_by_id(user_id)
        
        # Assert
        assert result is None
        mock_get_user_info.assert_called_once_with(user_id)

    @patch('domain.services.user_verification_service.verify_session_token')
    def test_verify_session_token_with_valid_user_object(self, mock_verify_session_token):
        """Test que retorna correctamente un objeto usuario válido."""
        # Arrange
        session_token = "valid_token"
        expected_user = Users(
            user_id=2,
            name="Another User",
            email="another@example.com",
            password_hash="another_hash",
            verification_token=None,
            user_state_id=1
        )
        mock_verify_session_token.return_value = expected_user
        
        # Act
        result = self.verification_service.verify_session_token(session_token)
        
        # Assert
        assert result == expected_user
        assert result.user_id == 2
        assert result.name == "Another User"
        assert result.email == "another@example.com"

    @patch.object(UserService, 'find_user_by_email')
    def test_verify_user_by_email_with_special_characters(self, mock_find_user):
        """Test que maneja emails con caracteres especiales."""
        # Arrange
        email = "test+special@example.com"
        user_with_special_email = User(
            user_id=3,
            name="Special User",
            email=email
        )
        mock_find_user.return_value = user_with_special_email
        
        # Act
        result = self.verification_service.verify_user_by_email(email)
        
        # Assert
        expected_result = {
            "user_id": 3,
            "name": "Special User",
            "email": email
        }
        assert result == expected_result

    @patch.object(UserService, 'get_user_info')
    def test_get_user_by_id_returns_complete_user_info(self, mock_get_user_info):
        """Test que retorna información completa del usuario."""
        # Arrange
        user_id = 5
        complete_user_info = {
            "user_id": 5,
            "name": "Complete User",
            "email": "complete@example.com",
            "user_state_id": 2,
            "is_verified": False,
            "is_suspended": True
        }
        mock_get_user_info.return_value = complete_user_info
        
        # Act
        result = self.verification_service.get_user_by_id(user_id)
        
        # Assert
        assert result == complete_user_info
        assert result["user_id"] == 5
        assert result["is_verified"] == False
        assert result["is_suspended"] == True

    # Additional edge case tests for better coverage

    @patch('domain.services.user_verification_service.verify_session_token')
    def test_verify_session_token_with_long_token(self, mock_verify_session_token):
        """Test que maneja tokens de sesión muy largos."""
        # Arrange
        long_token = "a" * 1000  # Token de 1000 caracteres
        mock_verify_session_token.return_value = self.sample_user
        
        # Act
        result = self.verification_service.verify_session_token(long_token)
        
        # Assert
        assert result == self.sample_user
        mock_verify_session_token.assert_called_once_with(long_token, self.mock_db)

    @patch('domain.services.user_verification_service.verify_session_token')
    def test_verify_session_token_with_special_characters(self, mock_verify_session_token):
        """Test que maneja tokens con caracteres especiales."""
        # Arrange
        special_token = "token_!@#$%^&*()_+-={}[]|\\:;\"'<>?,./"
        mock_verify_session_token.return_value = self.sample_user
        
        # Act
        result = self.verification_service.verify_session_token(special_token)
        
        # Assert
        assert result == self.sample_user
        mock_verify_session_token.assert_called_once_with(special_token, self.mock_db)

    @patch.object(UserService, 'find_user_by_email')
    def test_verify_user_by_email_with_unicode_characters(self, mock_find_user):
        """Test que maneja emails con caracteres unicode."""
        # Arrange
        unicode_email = "tést@exámple.com"
        user_with_unicode_email = User(
            user_id=4,
            name="Unicode User",
            email=unicode_email
        )
        mock_find_user.return_value = user_with_unicode_email
        
        # Act
        result = self.verification_service.verify_user_by_email(unicode_email)
        
        # Assert
        expected_result = {
            "user_id": 4,
            "name": "Unicode User",
            "email": unicode_email
        }
        assert result == expected_result

    @patch.object(UserService, 'get_user_info')
    def test_get_user_by_id_with_large_user_id(self, mock_get_user_info):
        """Test que maneja IDs de usuario muy grandes."""
        # Arrange
        large_user_id = 999999999
        user_info = {
            "user_id": large_user_id,
            "name": "Large ID User",
            "email": "large@example.com",
            "user_state_id": 1,
            "is_verified": True,
            "is_suspended": False
        }
        mock_get_user_info.return_value = user_info
        
        # Act
        result = self.verification_service.get_user_by_id(large_user_id)
        
        # Assert
        assert result == user_info
        mock_get_user_info.assert_called_once_with(large_user_id)

    @patch('domain.services.user_verification_service.verify_session_token')
    @patch('domain.services.user_verification_service.logger')
    def test_verify_session_token_unexpected_exception(self, mock_logger, mock_verify_session_token):
        """Test que maneja excepciones inesperadas en verificación de token."""
        # Arrange
        session_token = "test_token"
        unexpected_error = Exception("Unexpected error")
        mock_verify_session_token.side_effect = unexpected_error
        
        # Act & Assert
        with pytest.raises(Exception, match="Unexpected error"):
            self.verification_service.verify_session_token(session_token)
        
        # No se debe llamar al logger en este caso ya que solo captura SQLAlchemyError

    @patch.object(UserService, 'find_user_by_email')
    @patch('domain.services.user_verification_service.logger')
    def test_verify_user_by_email_unexpected_exception(self, mock_logger, mock_find_user):
        """Test que maneja excepciones inesperadas en verificación por email."""
        # Arrange
        email = "test@example.com"
        unexpected_error = Exception("Unexpected error")
        mock_find_user.side_effect = unexpected_error
        
        # Act & Assert
        with pytest.raises(Exception, match="Unexpected error"):
            self.verification_service.verify_user_by_email(email)

    @patch.object(UserService, 'get_user_info')
    @patch('domain.services.user_verification_service.logger')
    def test_get_user_by_id_unexpected_exception(self, mock_logger, mock_get_user_info):
        """Test que maneja excepciones inesperadas en obtención de usuario por ID."""
        # Arrange
        user_id = 1
        unexpected_error = Exception("Unexpected error")
        mock_get_user_info.side_effect = unexpected_error
        
        # Act & Assert
        with pytest.raises(Exception, match="Unexpected error"):
            self.verification_service.get_user_by_id(user_id)

    @patch.object(UserService, 'find_user_by_email')
    def test_verify_user_by_email_with_minimal_user_attributes(self, mock_find_user):
        """Test que maneja usuarios con atributos mínimos."""
        # Arrange
        email = "test@example.com"
        user_with_minimal_attributes = User(
            user_id=0,
            name="Minimal User",
            email=email
        )
        mock_find_user.return_value = user_with_minimal_attributes
        
        # Act
        result = self.verification_service.verify_user_by_email(email)
        
        # Assert
        expected_result = {
            "user_id": 0,
            "name": "Minimal User",
            "email": email
        }
        assert result == expected_result

    def test_user_verification_service_db_instance_is_preserved(self):
        """Test que la instancia de base de datos se preserva correctamente."""
        # Arrange & Act
        verification_service = UserVerificationService(self.mock_db)
        
        # Assert
        assert verification_service.db is self.mock_db
        assert verification_service.user_service.db is self.mock_db
        
        # Verificar que son la misma instancia
        assert id(verification_service.db) == id(self.mock_db)
        assert id(verification_service.user_service.db) == id(self.mock_db)

    @patch('domain.services.user_verification_service.verify_session_token')
    def test_verify_session_token_whitespace_token(self, mock_verify_session_token):
        """Test que maneja tokens con solo espacios en blanco."""
        # Arrange
        whitespace_token = "   \t\n   "
        mock_verify_session_token.return_value = None
        
        # Act & Assert
        with pytest.raises(ValueError, match="Token de sesión inválido o usuario no encontrado"):
            self.verification_service.verify_session_token(whitespace_token)
        
        mock_verify_session_token.assert_called_once_with(whitespace_token, self.mock_db)
