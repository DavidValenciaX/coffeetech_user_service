import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import pytest
from unittest.mock import patch
from fastapi import HTTPException
import orjson

from use_cases.update_profile_use_case import UpdateProfileUseCase
from tests.mockdb import MockDB, UserSessions, Users, UserStates
from domain.schemas import UpdateProfile

@pytest.fixture
def mock_db_session():
    """Fixture to provide a fresh MockDB instance for each test"""
    db = MockDB()
    return db

@pytest.fixture
def sample_user_and_session(mock_db_session):
    """Fixture to create a sample user and session for testing"""
    # Get verified state
    verified_state = mock_db_session.query(UserStates).filter(lambda s: s.name == 'Verificado').first()
    
    # Create a test user
    user = Users(
        user_id=1,
        name='Original Name',
        email='test@example.com',
        password_hash='hashed_password',
        verification_token=None,
        user_state_id=verified_state.user_state_id
    )
    mock_db_session.add(user)
    
    # Create a test session
    session = UserSessions(
        user_session_id=1,
        user_id=1,
        session_token='valid_session_token'
    )
    mock_db_session.add(session)
    
    return user, session

@patch('domain.services.token_service.verify_session_token')
def test_update_profile_success(mock_verify_session, mock_db_session, sample_user_and_session):
    """Test successful profile update with valid data"""
    # Arrange
    user, _ = sample_user_and_session
    mock_verify_session.return_value = user
    
    profile_update = UpdateProfile(new_name='Updated Name')
    session_token = 'valid_session_token'
    
    # Act
    use_case = UpdateProfileUseCase(mock_db_session)
    response_obj = use_case.execute(profile_update, session_token)
    response = orjson.loads(response_obj.body)
    
    # Assert
    assert response["status"] == "success"
    assert response["message"] == "Perfil actualizado exitosamente"
    
    # Verify user name was updated in database
    updated_user = mock_db_session.query(Users).filter(lambda u: u.user_id == 1).first()
    assert updated_user.name == 'Updated Name'
    
    # Verify commit was called
    assert mock_db_session.committed
    
    # Verify verify_session_token was called with correct parameters
    mock_verify_session.assert_called_once_with(session_token, mock_db_session)

@patch('domain.services.token_service.verify_session_token')
def test_update_profile_invalid_session_token(mock_verify_session, mock_db_session):
    """Test profile update with invalid session token"""
    # Arrange
    mock_verify_session.return_value = None
    
    profile_update = UpdateProfile(new_name='Updated Name')
    session_token = 'invalid_session_token'
    
    # Act
    use_case = UpdateProfileUseCase(mock_db_session)
    response_obj = use_case.execute(profile_update, session_token)
    response = orjson.loads(response_obj.body)
    
    # Assert
    assert response["status"] == "error"
    assert response["message"] == "Credenciales expiradas, cerrando sesión."
    
    # Verify commit was not called
    assert not mock_db_session.committed
    
    # Verify verify_session_token was called
    mock_verify_session.assert_called_once_with(session_token, mock_db_session)

@patch('domain.services.token_service.verify_session_token')
def test_update_profile_empty_name(mock_verify_session, mock_db_session, sample_user_and_session):
    """Test profile update with empty name"""
    # Arrange
    user, _ = sample_user_and_session
    mock_verify_session.return_value = user
    
    profile_update = UpdateProfile(new_name='')
    session_token = 'valid_session_token'
    
    # Act
    use_case = UpdateProfileUseCase(mock_db_session)
    response_obj = use_case.execute(profile_update, session_token)
    response = orjson.loads(response_obj.body)
    
    # Assert
    assert response["status"] == "error"
    assert "El nombre no puede estar vacío" in response["message"]
    
    # Verify user name was not updated
    original_user = mock_db_session.query(Users).filter(lambda u: u.user_id == 1).first()
    assert original_user.name == 'Original Name'
    
    # Verify commit was not called
    assert not mock_db_session.committed

@patch('domain.services.token_service.verify_session_token')
def test_update_profile_whitespace_only_name(mock_verify_session, mock_db_session, sample_user_and_session):
    """Test profile update with whitespace-only name"""
    # Arrange
    user, _ = sample_user_and_session
    mock_verify_session.return_value = user
    
    profile_update = UpdateProfile(new_name='   ')
    session_token = 'valid_session_token'
    
    # Act
    use_case = UpdateProfileUseCase(mock_db_session)
    response_obj = use_case.execute(profile_update, session_token)
    response = orjson.loads(response_obj.body)
    
    # Assert
    assert response["status"] == "error"
    assert "El nombre no puede estar vacío" in response["message"]
    
    # Verify user name was not updated
    original_user = mock_db_session.query(Users).filter(lambda u: u.user_id == 1).first()
    assert original_user.name == 'Original Name'

@patch('domain.services.token_service.verify_session_token')
def test_update_profile_name_too_short(mock_verify_session, mock_db_session, sample_user_and_session):
    """Test profile update with name that's too short (should succeed since no length validation exists)"""
    # Arrange
    user, _ = sample_user_and_session
    mock_verify_session.return_value = user
    
    profile_update = UpdateProfile(new_name='A')  # Single character
    session_token = 'valid_session_token'
    
    # Act
    use_case = UpdateProfileUseCase(mock_db_session)
    response_obj = use_case.execute(profile_update, session_token)
    response = orjson.loads(response_obj.body)
    
    # Assert
    assert response["status"] == "success"
    assert response["message"] == "Perfil actualizado exitosamente"
    
    # Verify user name was updated
    updated_user = mock_db_session.query(Users).filter(lambda u: u.user_id == 1).first()
    assert updated_user.name == 'A'

@patch('domain.services.token_service.verify_session_token')
def test_update_profile_name_too_long(mock_verify_session, mock_db_session, sample_user_and_session):
    """Test profile update with name that's too long (should succeed since no length validation exists)"""
    # Arrange
    user, _ = sample_user_and_session
    mock_verify_session.return_value = user
    
    long_name = 'A' * 51  # 51 characters
    profile_update = UpdateProfile(new_name=long_name)
    session_token = 'valid_session_token'
    
    # Act
    use_case = UpdateProfileUseCase(mock_db_session)
    response_obj = use_case.execute(profile_update, session_token)
    response = orjson.loads(response_obj.body)
    
    # Assert
    assert response["status"] == "success"
    assert response["message"] == "Perfil actualizado exitosamente"
    
    # Verify user name was updated
    updated_user = mock_db_session.query(Users).filter(lambda u: u.user_id == 1).first()
    assert updated_user.name == long_name

@patch('domain.services.token_service.verify_session_token')
def test_update_profile_name_with_numbers(mock_verify_session, mock_db_session, sample_user_and_session):
    """Test profile update with name containing numbers (should succeed since no character validation exists)"""
    # Arrange
    user, _ = sample_user_and_session
    mock_verify_session.return_value = user
    
    profile_update = UpdateProfile(new_name='John123')
    session_token = 'valid_session_token'
    
    # Act
    use_case = UpdateProfileUseCase(mock_db_session)
    response_obj = use_case.execute(profile_update, session_token)
    response = orjson.loads(response_obj.body)
    
    # Assert
    assert response["status"] == "success"
    assert response["message"] == "Perfil actualizado exitosamente"
    
    # Verify user name was updated
    updated_user = mock_db_session.query(Users).filter(lambda u: u.user_id == 1).first()
    assert updated_user.name == 'John123'

@patch('domain.services.token_service.verify_session_token')
def test_update_profile_name_with_special_characters(mock_verify_session, mock_db_session, sample_user_and_session):
    """Test profile update with name containing special characters (should succeed since no character validation exists)"""
    # Arrange
    user, _ = sample_user_and_session
    mock_verify_session.return_value = user
    
    profile_update = UpdateProfile(new_name='John@Doe')
    session_token = 'valid_session_token'
    
    # Act
    use_case = UpdateProfileUseCase(mock_db_session)
    response_obj = use_case.execute(profile_update, session_token)
    response = orjson.loads(response_obj.body)
    
    # Assert
    assert response["status"] == "success"
    assert response["message"] == "Perfil actualizado exitosamente"
    
    # Verify user name was updated
    updated_user = mock_db_session.query(Users).filter(lambda u: u.user_id == 1).first()
    assert updated_user.name == 'John@Doe'

@patch('domain.services.token_service.verify_session_token')
def test_update_profile_valid_name_with_spaces(mock_verify_session, mock_db_session, sample_user_and_session):
    """Test profile update with valid name containing spaces"""
    # Arrange
    user, _ = sample_user_and_session
    mock_verify_session.return_value = user
    
    profile_update = UpdateProfile(new_name='John Doe Smith')
    session_token = 'valid_session_token'
    
    # Act
    use_case = UpdateProfileUseCase(mock_db_session)
    response_obj = use_case.execute(profile_update, session_token)
    response = orjson.loads(response_obj.body)
    
    # Assert
    assert response["status"] == "success"
    assert response["message"] == "Perfil actualizado exitosamente"
    
    # Verify user name was updated
    updated_user = mock_db_session.query(Users).filter(lambda u: u.user_id == 1).first()
    assert updated_user.name == 'John Doe Smith'

@patch('domain.services.token_service.verify_session_token')
def test_update_profile_name_with_accents(mock_verify_session, mock_db_session, sample_user_and_session):
    """Test profile update with name containing accented characters"""
    # Arrange
    user, _ = sample_user_and_session
    mock_verify_session.return_value = user
    
    profile_update = UpdateProfile(new_name='José María')
    session_token = 'valid_session_token'
    
    # Act
    use_case = UpdateProfileUseCase(mock_db_session)
    response_obj = use_case.execute(profile_update, session_token)
    response = orjson.loads(response_obj.body)
    
    # Assert
    assert response["status"] == "success"
    assert response["message"] == "Perfil actualizado exitosamente"
    
    # Verify user name was updated
    updated_user = mock_db_session.query(Users).filter(lambda u: u.user_id == 1).first()
    assert updated_user.name == 'José María'

@patch('domain.services.token_service.verify_session_token')
def test_update_profile_database_error_on_commit(mock_verify_session, mock_db_session, sample_user_and_session):
    """Test profile update when database commit fails"""
    # Arrange
    user, _ = sample_user_and_session
    mock_verify_session.return_value = user
    
    profile_update = UpdateProfile(new_name='Updated Name')
    session_token = 'valid_session_token'
    
    # Configure mock to fail on commit
    mock_db_session.set_commit_fail(True, "Database connection lost")
    
    # Act & Assert
    use_case = UpdateProfileUseCase(mock_db_session)
    
    with pytest.raises(HTTPException) as exc_info:
        use_case.execute(profile_update, session_token)
    
    assert exc_info.value.status_code == 500
    assert "Error al actualizar el perfil" in str(exc_info.value.detail)
    assert "Database connection lost" in str(exc_info.value.detail)
    
    # Verify rollback was called
    assert mock_db_session.rolled_back

@patch('domain.services.token_service.verify_session_token')
def test_update_profile_same_name(mock_verify_session, mock_db_session, sample_user_and_session):
    """Test profile update with the same name (should still succeed)"""
    # Arrange
    user, _ = sample_user_and_session
    mock_verify_session.return_value = user
    
    profile_update = UpdateProfile(new_name='Original Name')  # Same as current name
    session_token = 'valid_session_token'
    
    # Act
    use_case = UpdateProfileUseCase(mock_db_session)
    response_obj = use_case.execute(profile_update, session_token)
    response = orjson.loads(response_obj.body)
    
    # Assert
    assert response["status"] == "success"
    assert response["message"] == "Perfil actualizado exitosamente"
    
    # Verify user name remains the same
    updated_user = mock_db_session.query(Users).filter(lambda u: u.user_id == 1).first()
    assert updated_user.name == 'Original Name'
    
    # Verify commit was called
    assert mock_db_session.committed

@patch('domain.services.token_service.verify_session_token')
def test_update_profile_minimum_valid_length(mock_verify_session, mock_db_session, sample_user_and_session):
    """Test profile update with minimum valid name length"""
    # Arrange
    user, _ = sample_user_and_session
    mock_verify_session.return_value = user
    
    profile_update = UpdateProfile(new_name='Jo')  # 2 characters (minimum)
    session_token = 'valid_session_token'
    
    # Act
    use_case = UpdateProfileUseCase(mock_db_session)
    response_obj = use_case.execute(profile_update, session_token)
    response = orjson.loads(response_obj.body)
    
    # Assert
    assert response["status"] == "success"
    assert response["message"] == "Perfil actualizado exitosamente"
    
    # Verify user name was updated
    updated_user = mock_db_session.query(Users).filter(lambda u: u.user_id == 1).first()
    assert updated_user.name == 'Jo'

@patch('domain.services.token_service.verify_session_token')
def test_update_profile_maximum_valid_length(mock_verify_session, mock_db_session, sample_user_and_session):
    """Test profile update with maximum valid name length"""
    # Arrange
    user, _ = sample_user_and_session
    mock_verify_session.return_value = user
    
    max_name = 'A' * 50  # 50 characters (maximum)
    profile_update = UpdateProfile(new_name=max_name)
    session_token = 'valid_session_token'
    
    # Act
    use_case = UpdateProfileUseCase(mock_db_session)
    response_obj = use_case.execute(profile_update, session_token)
    response = orjson.loads(response_obj.body)
    
    # Assert
    assert response["status"] == "success"
    assert response["message"] == "Perfil actualizado exitosamente"
    
    # Verify user name was updated
    updated_user = mock_db_session.query(Users).filter(lambda u: u.user_id == 1).first()
    assert updated_user.name == max_name

@patch('domain.services.token_service.verify_session_token')
def test_update_profile_name_with_leading_trailing_spaces(mock_verify_session, mock_db_session, sample_user_and_session):
    """Test profile update with name having leading/trailing spaces (spaces are preserved)"""
    # Arrange
    user, _ = sample_user_and_session
    mock_verify_session.return_value = user
    
    profile_update = UpdateProfile(new_name='  John Doe  ')
    session_token = 'valid_session_token'
    
    # Act
    use_case = UpdateProfileUseCase(mock_db_session)
    response_obj = use_case.execute(profile_update, session_token)
    response = orjson.loads(response_obj.body)
    
    # Assert
    assert response["status"] == "success"
    assert response["message"] == "Perfil actualizado exitosamente"
    
    # Verify user name was updated with spaces preserved
    updated_user = mock_db_session.query(Users).filter(lambda u: u.user_id == 1).first()
    assert updated_user.name == '  John Doe  '

@patch('domain.services.token_service.verify_session_token')
def test_update_profile_multiple_consecutive_spaces(mock_verify_session, mock_db_session, sample_user_and_session):
    """Test profile update with name having multiple consecutive spaces"""
    # Arrange
    user, _ = sample_user_and_session
    mock_verify_session.return_value = user
    
    profile_update = UpdateProfile(new_name='John    Doe')  # Multiple spaces
    session_token = 'valid_session_token'
    
    # Act
    use_case = UpdateProfileUseCase(mock_db_session)
    response_obj = use_case.execute(profile_update, session_token)
    response = orjson.loads(response_obj.body)
    
    # Assert
    assert response["status"] == "success"
    assert response["message"] == "Perfil actualizado exitosamente"
    
    # Verify user name was updated (spaces should be preserved as per current validation)
    updated_user = mock_db_session.query(Users).filter(lambda u: u.user_id == 1).first()
    assert updated_user.name == 'John    Doe' 