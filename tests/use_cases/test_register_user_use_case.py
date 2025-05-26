import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException
from sqlalchemy.orm import Session
from use_cases.register_user_use_case import RegisterUserUseCase
from models.models import Users
from domain.entities.user_entity import UserEntity


class TestRegisterUserUseCase:
    """Tests para la clase RegisterUserUseCase."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.mock_db = Mock(spec=Session)
        self.use_case = RegisterUserUseCase(self.mock_db)
        
        # Mock de user_data
        self.mock_user_data = Mock()
        self.mock_user_data.name = "Test User"
        self.mock_user_data.email = "test@example.com"
        self.mock_user_data.password = "TestPassword123!"
        self.mock_user_data.passwordConfirmation = "TestPassword123!"
    
    @patch('use_cases.register_user_use_case.create_response')
    def test_execute_validation_error(self, mock_create_response):
        """Test que retorna error cuando la validación falla."""
        # Arrange
        self.use_case.user_validator.validate_user_registration = Mock(return_value="Error de validación")
        mock_create_response.return_value = {"status": "error", "message": "Error de validación"}
        
        # Act
        result = self.use_case.execute(self.mock_user_data)
        
        # Assert
        mock_create_response.assert_called_once_with("error", "Error de validación")
        assert result["status"] == "error"
    
    @patch('use_cases.register_user_use_case.create_response')
    def test_execute_new_user_success(self, mock_create_response):
        """Test que crea un nuevo usuario exitosamente."""
        # Arrange
        self.use_case.user_validator.validate_user_registration = Mock(return_value=None)
        self.use_case.user_service.find_user_by_email = Mock(return_value=None)
        
        mock_user = Mock(spec=UserEntity)
        mock_user.verification_token = "token123"
        self.use_case.user_service.create_user = Mock(return_value=mock_user)
        self.use_case.notification_service.send_verification_email = Mock()
        
        mock_create_response.return_value = {"status": "success", "message": "Usuario creado"}
        
        # Act
        result = self.use_case.execute(self.mock_user_data)
        
        # Assert
        self.use_case.user_service.create_user.assert_called_once_with(
            self.mock_user_data.name,
            self.mock_user_data.email,
            self.mock_user_data.password
        )
        self.use_case.notification_service.send_verification_email.assert_called_once_with(
            self.mock_user_data.email,
            mock_user.verification_token
        )
        assert result["status"] == "success"
    
    @patch('use_cases.register_user_use_case.create_response')
    def test_execute_existing_user_unverified(self, mock_create_response):
        """Test que actualiza un usuario existente no verificado."""
        # Arrange
        self.use_case.user_validator.validate_user_registration = Mock(return_value=None)
        
        mock_existing_user = Mock(spec=UserEntity)
        mock_existing_user.is_unverified.return_value = True
        self.use_case.user_service.find_user_by_email = Mock(return_value=mock_existing_user)
        
        mock_updated_user = Mock(spec=UserEntity)
        mock_updated_user.verification_token = "new_token123"
        self.use_case.user_service.update_unverified_user = Mock(return_value=mock_updated_user)
        self.use_case.notification_service.send_verification_email = Mock()
        
        mock_create_response.return_value = {"status": "success", "message": "Usuario actualizado"}
        
        # Act
        result = self.use_case.execute(self.mock_user_data)
        
        # Assert
        self.use_case.user_service.update_unverified_user.assert_called_once_with(
            mock_existing_user,
            self.mock_user_data.name,
            self.mock_user_data.password
        )
        self.use_case.notification_service.send_verification_email.assert_called_once_with(
            self.mock_user_data.email,
            mock_updated_user.verification_token
        )
        assert result["status"] == "success"
    
    @patch('use_cases.register_user_use_case.create_response')
    def test_execute_existing_user_verified(self, mock_create_response):
        """Test que retorna error cuando el usuario ya está verificado."""
        # Arrange
        self.use_case.user_validator.validate_user_registration = Mock(return_value=None)
        
        mock_existing_user = Mock(spec=UserEntity)
        mock_existing_user.is_unverified.return_value = False
        self.use_case.user_service.find_user_by_email = Mock(return_value=mock_existing_user)
        
        mock_create_response.return_value = {"status": "error", "message": "El correo ya está registrado"}
        
        # Act
        result = self.use_case.execute(self.mock_user_data)
        
        # Assert
        mock_create_response.assert_called_once_with("error", "El correo ya está registrado")
        assert result["status"] == "error"
    
    def test_execute_exception_handling(self):
        """Test que maneja excepciones correctamente."""
        # Arrange
        self.use_case.user_validator.validate_user_registration = Mock(side_effect=Exception("Test error"))
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            self.use_case.execute(self.mock_user_data)
        
        assert exc_info.value.status_code == 500
        assert "Error interno del servidor" in str(exc_info.value.detail)
    
    def test_validate_user_data(self):
        """Test del método de validación de datos."""
        # Arrange
        self.use_case.user_validator.validate_user_registration = Mock(return_value="Error de validación")
        
        # Act
        result = self.use_case._validate_user_data(self.mock_user_data)
        
        # Assert
        self.use_case.user_validator.validate_user_registration.assert_called_once_with(
            self.mock_user_data.name,
            self.mock_user_data.password,
            self.mock_user_data.passwordConfirmation
        )
        assert result == "Error de validación" 