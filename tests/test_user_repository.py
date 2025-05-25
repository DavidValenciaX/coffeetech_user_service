import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from domain.repositories import UserRepository
from models.models import Users, UserStates


class TestUserRepository:
    """Tests para la clase UserRepository."""
    
    def setup_method(self):
        """Setup para cada test."""
        self.mock_db = Mock(spec=Session)
        self.repository = UserRepository(self.mock_db)
    
    def test_find_by_email_found(self):
        """Test que encuentra un usuario por email."""
        # Arrange
        expected_user = Mock(spec=Users)
        expected_user.email = "test@example.com"
        self.mock_db.query.return_value.filter.return_value.first.return_value = expected_user
        
        # Act
        result = self.repository.find_by_email("test@example.com")
        
        # Assert
        assert result == expected_user
        self.mock_db.query.assert_called_once_with(Users)
    
    def test_find_by_email_not_found(self):
        """Test que no encuentra un usuario por email."""
        # Arrange
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Act
        result = self.repository.find_by_email("nonexistent@example.com")
        
        # Assert
        assert result is None
    
    @patch('domain.repositories.get_user_state')
    def test_get_unverified_state_found(self, mock_get_user_state):
        """Test que obtiene el estado no verificado."""
        # Arrange
        expected_state = Mock(spec=UserStates)
        expected_state.user_state_id = 1
        mock_get_user_state.return_value = expected_state
        
        # Act
        result = self.repository.get_unverified_state()
        
        # Assert
        assert result == expected_state
        mock_get_user_state.assert_called_once_with(self.mock_db, "No Verificado")
    
    @patch('domain.repositories.get_user_state')
    def test_get_unverified_state_not_found(self, mock_get_user_state):
        """Test que no encuentra el estado no verificado."""
        # Arrange
        mock_get_user_state.return_value = None
        
        # Act
        result = self.repository.get_unverified_state()
        
        # Assert
        assert result is None
    
    @patch('domain.repositories.hash_password')
    @patch('domain.repositories.generate_verification_token')
    @patch('domain.repositories.get_user_state')
    def test_create_user_success(self, mock_get_user_state, mock_generate_token, mock_hash_password):
        """Test que crea un usuario exitosamente."""
        # Arrange
        mock_hash_password.return_value = "hashed_password"
        mock_generate_token.return_value = "verification_token"
        
        mock_state = Mock(spec=UserStates)
        mock_state.user_state_id = 1
        mock_get_user_state.return_value = mock_state
        
        mock_user = Mock(spec=Users)
        mock_user.name = "Test User"
        mock_user.email = "test@example.com"
        mock_user.password_hash = "hashed_password"
        mock_user.verification_token = "verification_token"
        mock_user.user_state_id = 1
        
        # Simular que el usuario creado es mock_user
        with patch.object(self.repository, 'db') as mock_db:
            mock_db.add = Mock()
            mock_db.commit = Mock()
            mock_db.refresh = Mock()
            
            # Simular la creación del objeto Users
            with patch('domain.repositories.Users', return_value=mock_user):
                # Act
                result = self.repository.create_user("Test User", "test@example.com", "password123")
                
                # Assert
                assert result == mock_user
                assert result.name == "Test User"
                assert result.email == "test@example.com"
                assert result.password_hash == "hashed_password"
                assert result.verification_token == "verification_token"
                assert result.user_state_id == 1
                
                mock_db.add.assert_called_once_with(mock_user)
                mock_db.commit.assert_called_once()
                mock_db.refresh.assert_called_once_with(mock_user)
                mock_hash_password.assert_called_once_with("password123")
                mock_generate_token.assert_called_once_with(4)
    
    @patch('domain.repositories.get_user_state')
    def test_create_user_no_unverified_state(self, mock_get_user_state):
        """Test que falla al crear usuario si no existe el estado no verificado."""
        # Arrange
        mock_get_user_state.return_value = None
        
        # Act & Assert
        with pytest.raises(Exception, match="No se encontró el estado 'No Verificado' para usuarios"):
            self.repository.create_user("Test User", "test@example.com", "password123")
    
    @patch('domain.repositories.hash_password')
    @patch('domain.repositories.generate_verification_token')
    def test_update_unverified_user_success(self, mock_generate_token, mock_hash_password):
        """Test que actualiza un usuario no verificado exitosamente."""
        # Arrange
        mock_hash_password.return_value = "new_hashed_password"
        mock_generate_token.return_value = "new_verification_token"
        
        mock_user = Mock(spec=Users)
        mock_user.email = "test@example.com"
        
        # Act
        result = self.repository.update_unverified_user(mock_user, "New Name", "new_password")
        
        # Assert
        assert result == mock_user
        assert result.name == "New Name"
        assert result.password_hash == "new_hashed_password"
        assert result.verification_token == "new_verification_token"
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once_with(mock_user)
    
    @patch('domain.repositories.get_user_state')
    def test_is_user_unverified_true(self, mock_get_user_state):
        """Test que verifica correctamente si un usuario está no verificado."""
        # Arrange
        mock_state = Mock(spec=UserStates)
        mock_state.user_state_id = 1
        mock_get_user_state.return_value = mock_state
        
        mock_user = Mock(spec=Users)
        mock_user.user_state_id = 1
        
        # Act
        result = self.repository.is_user_unverified(mock_user)
        
        # Assert
        assert result is True
    
    @patch('domain.repositories.get_user_state')
    def test_is_user_unverified_false(self, mock_get_user_state):
        """Test que verifica correctamente si un usuario no está no verificado."""
        # Arrange
        mock_state = Mock(spec=UserStates)
        mock_state.user_state_id = 1
        mock_get_user_state.return_value = mock_state
        
        mock_user = Mock(spec=Users)
        mock_user.user_state_id = 2  # Diferente estado
        
        # Act
        result = self.repository.is_user_unverified(mock_user)
        
        # Assert
        assert result is False 