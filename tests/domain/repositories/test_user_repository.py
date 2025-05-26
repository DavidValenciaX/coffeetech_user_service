import sys
import os
import pytest
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from domain.repositories.user_repository import UserRepository
from models.models import Users, UserStates, UserSessions, UserDevices, UserRole, Roles
from tests.mockdb import MockDB


class TestUserRepository:
    """Tests para la clase UserRepository."""
    
    def setup_method(self):
        """Configuración previa a cada test."""
        self.mock_db = MockDB()
        self.repository = UserRepository(self.mock_db)
        
        # Datos de prueba
        self.test_user_data = {
            'user_id': 1,
            'name': 'Juan Pérez',
            'email': 'juan@example.com',
            'password_hash': 'hashed_password_123',
            'verification_token': 'token_123',
            'user_state_id': 1
        }
        
        self.test_user = Users(**self.test_user_data)
        self.test_user.user_state = UserStates(user_state_id=1, name='Verificado')
        self.test_user.roles = []
        self.test_user.sessions = []
        self.test_user.devices = []

    def test_find_by_email_found(self):
        """Test que encuentra un usuario por email exitosamente."""
        # Arrange
        self.mock_db.users.append(self.test_user)
        
        # Act
        result = self.repository.find_by_email('juan@example.com')
        
        # Assert
        assert result is not None
        assert result.email == 'juan@example.com'
        assert result.name == 'Juan Pérez'

    def test_find_by_email_not_found(self):
        """Test que retorna None cuando no encuentra el usuario por email."""
        # Act
        result = self.repository.find_by_email('nonexistent@example.com')
        
        # Assert
        assert result is None

    def test_find_by_email_empty_database(self):
        """Test que retorna None cuando la base de datos está vacía."""
        # Act
        result = self.repository.find_by_email('any@example.com')
        
        # Assert
        assert result is None

    def test_find_by_id_found(self):
        """Test que encuentra un usuario por ID exitosamente."""
        # Arrange
        self.mock_db.users.append(self.test_user)
        
        # Act
        result = self.repository.find_by_id(1)
        
        # Assert
        assert result is not None
        assert result.user_id == 1
        assert result.name == 'Juan Pérez'

    def test_find_by_id_not_found(self):
        """Test que retorna None cuando no encuentra el usuario por ID."""
        # Act
        result = self.repository.find_by_id(999)
        
        # Assert
        assert result is None

    def test_find_by_verification_token_found(self):
        """Test que encuentra un usuario por token de verificación exitosamente."""
        # Arrange
        self.mock_db.users.append(self.test_user)
        
        # Act
        result = self.repository.find_by_verification_token('token_123')
        
        # Assert
        assert result is not None
        assert result.verification_token == 'token_123'
        assert result.email == 'juan@example.com'

    def test_find_by_verification_token_not_found(self):
        """Test que retorna None cuando no encuentra el usuario por token."""
        # Act
        result = self.repository.find_by_verification_token('invalid_token')
        
        # Assert
        assert result is None

    def test_create_user_success(self):
        """Test que crea un usuario exitosamente."""
        # Arrange
        user_data = {
            'name': 'María López',
            'email': 'maria@example.com',
            'password_hash': 'hashed_password_456',
            'verification_token': 'token_456',
            'user_state_id': 2
        }
        
        # Act
        result = self.repository.create(user_data)
        
        # Assert
        assert result is not None
        assert result.name == 'María López'
        assert result.email == 'maria@example.com'
        assert len(self.mock_db.users) == 1
        assert self.mock_db.committed

    def test_create_user_with_refresh_mock(self):
        """Test que maneja correctamente el refresh después de crear."""
        # Arrange
        user_data = {
            'name': 'Pedro García',
            'email': 'pedro@example.com',
            'password_hash': 'hashed_password_789',
            'verification_token': 'token_789',
            'user_state_id': 1
        }
        
        # Mock refresh method
        with patch.object(self.mock_db, 'refresh') as mock_refresh:
            # Act
            result = self.repository.create(user_data)
            
            # Assert
            assert result is not None
            assert result.email == 'pedro@example.com'
            mock_refresh.assert_called_once()

    def test_create_user_commit_failure(self):
        """Test que maneja errores durante el commit."""
        # Arrange
        self.mock_db.set_commit_fail(True, "Database connection error")
        user_data = {
            'name': 'Error User',
            'email': 'error@example.com',
            'password_hash': 'hashed_password',
            'verification_token': 'error_token',
            'user_state_id': 1
        }
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            self.repository.create(user_data)
        
        assert "Database connection error" in str(exc_info.value)
        assert self.mock_db.rolled_back

    def test_create_user_general_exception(self):
        """Test que maneja excepciones generales durante la creación."""
        # Arrange
        with patch.object(self.mock_db, 'add', side_effect=Exception("General error")):
            user_data = {
                'name': 'Exception User',
                'email': 'exception@example.com',
                'password_hash': 'hashed_password',
                'verification_token': 'exception_token',
                'user_state_id': 1
            }
            
            # Act & Assert
            with pytest.raises(Exception) as exc_info:
                self.repository.create(user_data)
            
            assert "General error" in str(exc_info.value)

    def test_update_user_success(self):
        """Test que actualiza un usuario exitosamente."""
        # Arrange
        self.mock_db.users.append(self.test_user)
        update_data = {
            'name': 'Juan Carlos Pérez',
            'verification_token': 'new_token_123'
        }
        
        # Act
        result = self.repository.update(self.test_user, update_data)
        
        # Assert
        assert result is not None
        assert result.name == 'Juan Carlos Pérez'
        assert result.verification_token == 'new_token_123'
        assert result.email == 'juan@example.com'  # No cambió
        assert self.mock_db.committed

    def test_update_user_empty_data(self):
        """Test que maneja actualizaciones con datos vacíos."""
        # Arrange
        self.mock_db.users.append(self.test_user)
        update_data = {}
        
        # Act
        result = self.repository.update(self.test_user, update_data)
        
        # Assert
        assert result is not None
        assert result.name == 'Juan Pérez'  # Sin cambios
        assert self.mock_db.committed

    def test_update_user_invalid_attribute(self):
        """Test que ignora atributos inválidos durante la actualización."""
        # Arrange
        self.mock_db.users.append(self.test_user)
        update_data = {
            'name': 'Nuevo Nombre',
            'invalid_field': 'valor_invalido'
        }
        
        # Act
        result = self.repository.update(self.test_user, update_data)
        
        # Assert
        assert result is not None
        assert result.name == 'Nuevo Nombre'
        assert not hasattr(result, 'invalid_field')

    def test_update_user_commit_failure(self):
        """Test que maneja errores durante el commit de actualización."""
        # Arrange
        self.mock_db.users.append(self.test_user)
        self.mock_db.set_commit_fail(True, "Update commit failed")
        update_data = {'name': 'Failed Update'}
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            self.repository.update(self.test_user, update_data)
        
        assert "Update commit failed" in str(exc_info.value)
        assert self.mock_db.rolled_back

    def test_delete_user_success(self):
        """Test que elimina un usuario exitosamente."""
        # Arrange
        self.mock_db.users.append(self.test_user)
        
        # Agregar datos relacionados
        session = UserSessions(user_session_id=1, user_id=1, session_token='session_token_123')
        device = UserDevices(user_device_id=1, user_id=1, fcm_token='fcm_token_123')
        role = UserRole(user_role_id=1, user_id=1, role_id=1)
        
        self.mock_db.user_sessions.append(session)
        self.mock_db.user_devices.append(device)
        self.mock_db.user_roles.append(role)
        
        # Act
        self.repository.delete(self.test_user)
        
        # Assert
        assert len(self.mock_db.users) == 0
        assert len(self.mock_db.user_sessions) == 0
        assert len(self.mock_db.user_devices) == 0
        assert len(self.mock_db.user_roles) == 0
        assert self.mock_db.committed

    def test_delete_user_with_multiple_relations(self):
        """Test que elimina un usuario con múltiples relaciones."""
        # Arrange
        self.mock_db.users.append(self.test_user)
        
        # Agregar múltiples relaciones
        sessions = [
            UserSessions(user_session_id=1, user_id=1, session_token='session_token_1'),
            UserSessions(user_session_id=2, user_id=1, session_token='session_token_2')
        ]
        devices = [
            UserDevices(user_device_id=1, user_id=1, fcm_token='fcm_token_1'),
            UserDevices(user_device_id=2, user_id=1, fcm_token='fcm_token_2')
        ]
        roles = [
            UserRole(user_role_id=1, user_id=1, role_id=1),
            UserRole(user_role_id=2, user_id=1, role_id=2)
        ]
        
        self.mock_db.user_sessions.extend(sessions)
        self.mock_db.user_devices.extend(devices)
        self.mock_db.user_roles.extend(roles)
        
        # Act
        self.repository.delete(self.test_user)
        
        # Assert
        assert len(self.mock_db.users) == 0
        assert len(self.mock_db.user_sessions) == 0
        assert len(self.mock_db.user_devices) == 0
        assert len(self.mock_db.user_roles) == 0

    def test_delete_user_no_relations(self):
        """Test que elimina un usuario sin relaciones."""
        # Arrange
        self.mock_db.users.append(self.test_user)
        
        # Act
        self.repository.delete(self.test_user)
        
        # Assert
        assert len(self.mock_db.users) == 0
        assert self.mock_db.committed

    def test_delete_user_commit_failure(self):
        """Test que maneja errores durante el commit de eliminación."""
        # Arrange
        self.mock_db.users.append(self.test_user)
        self.mock_db.set_commit_fail(True, "Delete commit failed")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            self.repository.delete(self.test_user)
        
        assert "Delete commit failed" in str(exc_info.value)
        assert self.mock_db.rolled_back

    def test_delete_user_with_other_users_data(self):
        """Test que solo elimina los datos del usuario específico."""
        # Arrange
        # Usuario 1
        self.mock_db.users.append(self.test_user)
        
        # Usuario 2
        other_user = Users(user_id=2, name='Otro Usuario', email='otro@example.com', 
                          password_hash='hash', verification_token='token2', user_state_id=1)
        self.mock_db.users.append(other_user)
        
        # Datos del usuario 1
        session1 = UserSessions(user_session_id=1, user_id=1, session_token='session_token_1')
        device1 = UserDevices(user_device_id=1, user_id=1, fcm_token='fcm_token_1')
        role1 = UserRole(user_role_id=1, user_id=1, role_id=1)
        
        # Datos del usuario 2
        session2 = UserSessions(user_session_id=2, user_id=2, session_token='session_token_2')
        device2 = UserDevices(user_device_id=2, user_id=2, fcm_token='fcm_token_2')
        role2 = UserRole(user_role_id=2, user_id=2, role_id=1)
        
        self.mock_db.user_sessions.extend([session1, session2])
        self.mock_db.user_devices.extend([device1, device2])
        self.mock_db.user_roles.extend([role1, role2])
        
        # Act
        self.repository.delete(self.test_user)
        
        # Assert
        assert len(self.mock_db.users) == 1
        assert self.mock_db.users[0].user_id == 2
        assert len(self.mock_db.user_sessions) == 1
        assert self.mock_db.user_sessions[0].user_id == 2
        assert len(self.mock_db.user_devices) == 1
        assert self.mock_db.user_devices[0].user_id == 2
        assert len(self.mock_db.user_roles) == 1
        assert self.mock_db.user_roles[0].user_id == 2

    @patch('domain.repositories.user_repository.logger')
    def test_create_user_logs_success(self, mock_logger):
        """Test que registra logs cuando se crea un usuario exitosamente."""
        # Arrange
        user_data = {
            'name': 'Log User',
            'email': 'log@example.com',
            'password_hash': 'hashed_password',
            'verification_token': 'log_token',
            'user_state_id': 1
        }
        
        # Act
        self.repository.create(user_data)
        
        # Assert
        mock_logger.info.assert_called_with("Usuario creado exitosamente: log@example.com")

    @patch('domain.repositories.user_repository.logger')
    def test_create_user_logs_error(self, mock_logger):
        """Test que registra logs cuando hay error al crear usuario."""
        # Arrange
        self.mock_db.set_commit_fail(True, "Test error")
        user_data = {
            'name': 'Error User',
            'email': 'error@example.com',
            'password_hash': 'hashed_password',
            'verification_token': 'error_token',
            'user_state_id': 1
        }
        
        # Act & Assert
        with pytest.raises(Exception):
            self.repository.create(user_data)
        
        mock_logger.error.assert_called()
        error_call_args = mock_logger.error.call_args[0][0]
        assert "Error al crear usuario:" in error_call_args

    @patch('domain.repositories.user_repository.logger')
    def test_update_user_logs_success(self, mock_logger):
        """Test que registra logs cuando se actualiza un usuario exitosamente."""
        # Arrange
        self.mock_db.users.append(self.test_user)
        update_data = {'name': 'Updated Name'}
        
        # Act
        self.repository.update(self.test_user, update_data)
        
        # Assert
        mock_logger.info.assert_called_with("Usuario actualizado exitosamente: juan@example.com")

    @patch('domain.repositories.user_repository.logger')
    def test_update_user_logs_error(self, mock_logger):
        """Test que registra logs cuando hay error al actualizar usuario."""
        # Arrange
        self.mock_db.users.append(self.test_user)
        self.mock_db.set_commit_fail(True, "Update error")
        update_data = {'name': 'Failed Update'}
        
        # Act & Assert
        with pytest.raises(Exception):
            self.repository.update(self.test_user, update_data)
        
        mock_logger.error.assert_called()
        error_call_args = mock_logger.error.call_args[0][0]
        assert "Error al actualizar usuario:" in error_call_args

    @patch('domain.repositories.user_repository.logger')
    def test_delete_user_logs_success(self, mock_logger):
        """Test que registra logs cuando se elimina un usuario exitosamente."""
        # Arrange
        self.mock_db.users.append(self.test_user)
        
        # Act
        self.repository.delete(self.test_user)
        
        # Assert
        mock_logger.info.assert_called_with("Usuario eliminado exitosamente: juan@example.com")

    @patch('domain.repositories.user_repository.logger')
    def test_delete_user_logs_error(self, mock_logger):
        """Test que registra logs cuando hay error al eliminar usuario."""
        # Arrange
        self.mock_db.users.append(self.test_user)
        self.mock_db.set_commit_fail(True, "Delete error")
        
        # Act & Assert
        with pytest.raises(Exception):
            self.repository.delete(self.test_user)
        
        mock_logger.error.assert_called()
        error_call_args = mock_logger.error.call_args[0][0]
        assert "Error al eliminar usuario:" in error_call_args

    def test_find_methods_with_relationships_loaded(self):
        """Test que verifica que los métodos find cargan las relaciones correctamente."""
        # Arrange
        self.mock_db.users.append(self.test_user)
        
        # Act & Assert para find_by_email
        result = self.repository.find_by_email('juan@example.com')
        assert hasattr(result, 'user_state')
        assert hasattr(result, 'roles')
        assert hasattr(result, 'sessions')
        assert hasattr(result, 'devices')
        
        # Act & Assert para find_by_id
        result = self.repository.find_by_id(1)
        assert hasattr(result, 'user_state')
        assert hasattr(result, 'roles')
        assert hasattr(result, 'sessions')
        assert hasattr(result, 'devices')
        
        # Act & Assert para find_by_verification_token
        result = self.repository.find_by_verification_token('token_123')
        assert hasattr(result, 'user_state')
        assert hasattr(result, 'roles')
        assert hasattr(result, 'sessions')
        assert hasattr(result, 'devices')
