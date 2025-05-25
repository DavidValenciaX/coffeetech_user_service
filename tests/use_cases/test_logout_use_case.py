import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException
import orjson

from use_cases.logout_use_case import LogoutUseCase
from tests.mockdb import MockDB, UserSessions, Users, UserStates
from domain.schemas import LogoutRequest

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
        name='Test User',
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
        session_token='test_session_token_12345'
    )
    mock_db_session.add(session)
    
    return user, session

def test_logout_success(mock_db_session, sample_user_and_session):
    """Test successful logout with valid session token"""
    # Arrange
    user, session = sample_user_and_session
    
    logout_request = LogoutRequest(session_token='test_session_token_12345')
    
    # Act
    use_case = LogoutUseCase(mock_db_session)
    response_obj = use_case.execute(logout_request)
    response = orjson.loads(response_obj.body)
    
    # Assert
    assert response["status"] == "success"
    assert response["message"] == "Cierre de sesión exitoso"
    
    # Verify session was deleted from database
    deleted_session = mock_db_session.query(UserSessions).filter(
        lambda s: s.session_token == 'test_session_token_12345'
    ).first()
    assert deleted_session is None
    
    # Verify commit was called
    assert mock_db_session.committed

def test_logout_invalid_session_token(mock_db_session):
    """Test logout with non-existent session token"""
    # Arrange
    logout_request = LogoutRequest(session_token='invalid_token_12345')
    
    # Act
    use_case = LogoutUseCase(mock_db_session)
    response_obj = use_case.execute(logout_request)
    response = orjson.loads(response_obj.body)
    
    # Assert
    assert response["status"] == "error"
    assert response["message"] == "Credenciales expiradas, cerrando sesión."
    
    # Verify commit was not called
    assert not mock_db_session.committed

def test_logout_empty_session_token(mock_db_session):
    """Test logout with empty session token"""
    # Arrange
    logout_request = LogoutRequest(session_token='')
    
    # Act
    use_case = LogoutUseCase(mock_db_session)
    response_obj = use_case.execute(logout_request)
    response = orjson.loads(response_obj.body)
    
    # Assert
    assert response["status"] == "error"
    assert response["message"] == "Credenciales expiradas, cerrando sesión."
    
    # Verify commit was not called
    assert not mock_db_session.committed

def test_logout_database_error_on_delete(mock_db_session, sample_user_and_session):
    """Test logout when database delete operation fails"""
    # Arrange
    user, session = sample_user_and_session
    logout_request = LogoutRequest(session_token='test_session_token_12345')
    
    # Configure mock to fail on commit
    mock_db_session.set_commit_fail(True, "Database connection lost")
    
    # Act & Assert
    use_case = LogoutUseCase(mock_db_session)
    
    with pytest.raises(HTTPException) as exc_info:
        use_case.execute(logout_request)
    
    assert exc_info.value.status_code == 500
    assert "Error durante el cierre de sesión" in str(exc_info.value.detail)
    
    # Verify rollback was called
    assert mock_db_session.rolled_back

def test_logout_database_error_on_commit(mock_db_session, sample_user_and_session):
    """Test logout when database commit operation fails"""
    # Arrange
    user, session = sample_user_and_session
    logout_request = LogoutRequest(session_token='test_session_token_12345')
    
    # Configure mock to fail on commit
    mock_db_session.set_commit_fail(True, "Database timeout")
    
    # Act & Assert
    use_case = LogoutUseCase(mock_db_session)
    
    with pytest.raises(HTTPException) as exc_info:
        use_case.execute(logout_request)
    
    assert exc_info.value.status_code == 500
    assert "Error durante el cierre de sesión" in str(exc_info.value.detail)
    assert "Database timeout" in str(exc_info.value.detail)
    
    # Verify rollback was called
    assert mock_db_session.rolled_back

def test_logout_multiple_sessions_same_user(mock_db_session):
    """Test logout only removes the specific session, not all user sessions"""
    # Arrange
    verified_state = mock_db_session.query(UserStates).filter(lambda s: s.name == 'Verificado').first()
    
    user = Users(
        user_id=1,
        name='Test User',
        email='test@example.com',
        password_hash='hashed_password',
        verification_token=None,
        user_state_id=verified_state.user_state_id
    )
    mock_db_session.add(user)
    
    # Create multiple sessions for the same user
    session1 = UserSessions(
        user_session_id=1,
        user_id=1,
        session_token='session_token_1'
    )
    session2 = UserSessions(
        user_session_id=2,
        user_id=1,
        session_token='session_token_2'
    )
    mock_db_session.add(session1)
    mock_db_session.add(session2)
    
    logout_request = LogoutRequest(session_token='session_token_1')
    
    # Act
    use_case = LogoutUseCase(mock_db_session)
    response_obj = use_case.execute(logout_request)
    response = orjson.loads(response_obj.body)
    
    # Assert
    assert response["status"] == "success"
    assert response["message"] == "Cierre de sesión exitoso"
    
    # Verify only the specific session was deleted
    deleted_session = mock_db_session.query(UserSessions).filter(
        lambda s: s.session_token == 'session_token_1'
    ).first()
    assert deleted_session is None
    
    # Verify the other session still exists
    remaining_session = mock_db_session.query(UserSessions).filter(
        lambda s: s.session_token == 'session_token_2'
    ).first()
    assert remaining_session is not None
    assert remaining_session.session_token == 'session_token_2'

def test_logout_with_very_long_session_token(mock_db_session, sample_user_and_session):
    """Test logout with a very long session token"""
    # Arrange
    user, session = sample_user_and_session
    
    # Update session with a very long token
    long_token = 'a' * 255  # Maximum length token
    session.session_token = long_token
    
    logout_request = LogoutRequest(session_token=long_token)
    
    # Act
    use_case = LogoutUseCase(mock_db_session)
    response_obj = use_case.execute(logout_request)
    response = orjson.loads(response_obj.body)
    
    # Assert
    assert response["status"] == "success"
    assert response["message"] == "Cierre de sesión exitoso"
    
    # Verify session was deleted
    deleted_session = mock_db_session.query(UserSessions).filter(
        lambda s: s.session_token == long_token
    ).first()
    assert deleted_session is None

def test_logout_case_sensitive_token(mock_db_session, sample_user_and_session):
    """Test that logout is case-sensitive for session tokens"""
    # Arrange
    user, session = sample_user_and_session
    
    # Try to logout with different case
    logout_request = LogoutRequest(session_token='TEST_SESSION_TOKEN_12345')
    
    # Act
    use_case = LogoutUseCase(mock_db_session)
    response_obj = use_case.execute(logout_request)
    response = orjson.loads(response_obj.body)
    
    # Assert
    assert response["status"] == "error"
    assert response["message"] == "Credenciales expiradas, cerrando sesión."
    
    # Verify original session still exists
    original_session = mock_db_session.query(UserSessions).filter(
        lambda s: s.session_token == 'test_session_token_12345'
    ).first()
    assert original_session is not None

def test_logout_with_special_characters_in_token(mock_db_session):
    """Test logout with special characters in session token"""
    # Arrange
    verified_state = mock_db_session.query(UserStates).filter(lambda s: s.name == 'Verificado').first()
    
    user = Users(
        user_id=1,
        name='Test User',
        email='test@example.com',
        password_hash='hashed_password',
        verification_token=None,
        user_state_id=verified_state.user_state_id
    )
    mock_db_session.add(user)
    
    special_token = 'token_with_!@#$%^&*()_+-={}[]|\\:";\'<>?,./'
    session = UserSessions(
        user_session_id=1,
        user_id=1,
        session_token=special_token
    )
    mock_db_session.add(session)
    
    logout_request = LogoutRequest(session_token=special_token)
    
    # Act
    use_case = LogoutUseCase(mock_db_session)
    response_obj = use_case.execute(logout_request)
    response = orjson.loads(response_obj.body)
    
    # Assert
    assert response["status"] == "success"
    assert response["message"] == "Cierre de sesión exitoso"
    
    # Verify session was deleted
    deleted_session = mock_db_session.query(UserSessions).filter(
        lambda s: s.session_token == special_token
    ).first()
    assert deleted_session is None 