import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
import orjson
from sqlalchemy.exc import OperationalError

from use_cases.login_use_case import login
from tests.mockdb import MockDB, UserSessions, Users, UserDevices, UserStates

@pytest.fixture
def mock_db_session():
    # Instantiate MockDB from mockdb.py
    db = MockDB()
    return db

@patch('use_cases.login_use_case.verify_password', return_value=True)
@patch('use_cases.login_use_case.generate_verification_token', return_value='test_session_token')
@patch('use_cases.login_use_case.get_user_state')
def test_login_success(mock_get_user_state, mock_generate_token, mock_verify_password, mock_db_session):
    
    # Arrange
    # Get the "Verificado" state from the mock database
    verified_state = mock_db_session.query(UserStates).filter(lambda s: s.name == 'Verificado').first()
    
    mock_user_data = Users(
        user_id=1,
        email='test@example.com',
        password_hash='hashed_password',
        name='Test User',
        user_state_id=verified_state.user_state_id,
        verification_token=None
    )
    mock_db_session.add(mock_user_data)

    # Configure mock to return the verified state
    mock_get_user_state.return_value = verified_state
    
    login_request = MagicMock()
    login_request.email = 'test@example.com'
    login_request.password = 'password123'
    login_request.fcm_token = 'test_fcm_token'

    # Act
    response_obj = login(login_request, mock_db_session)
    response = orjson.loads(response_obj.body)

    # Assert
    assert response["status"] == "success"
    assert response["message"] == "Inicio de sesión exitoso"
    assert response["data"]["session_token"] == "test_session_token"
    assert response["data"]["name"] == "Test User"
    
    # Check if UserDevices was added if fcm_token is present
    if login_request.fcm_token:
        added_device = mock_db_session.query(UserDevices).filter(
            lambda d: d.user_id == mock_user_data.user_id and d.fcm_token == login_request.fcm_token
        ).first()
        assert added_device is not None
        assert added_device.fcm_token == login_request.fcm_token

    # Check if a UserSession was added
    added_session = mock_db_session.query(UserSessions).filter(
        lambda s: s.user_id == mock_user_data.user_id and s.session_token == "test_session_token"
    ).first()
    assert added_session is not None
    assert added_session.session_token == "test_session_token"
    assert added_session.user_id == mock_user_data.user_id

    assert mock_db_session.committed # Check if commit was called

@patch('use_cases.login_use_case.verify_password', return_value=False)
def test_login_incorrect_credentials(mock_verify_password, mock_db_session):
    # Arrange
    # Get the "Verificado" state from the mock database 
    verified_state = mock_db_session.query(UserStates).filter(lambda s: s.name == 'Verificado').first()
    
    mock_user_data = Users(
        user_id=1,
        email='test@example.com',
        password_hash='hashed_password',
        name='Test User',
        user_state_id=verified_state.user_state_id,
        verification_token=None
    )
    mock_db_session.add(mock_user_data)

    login_request = MagicMock()
    login_request.email = 'test@example.com'
    login_request.password = 'wrong_password'

    # Act
    response_obj = login(login_request, mock_db_session)
    response = orjson.loads(response_obj.body)

    # Assert
    assert response["status"] == "error"
    assert response["message"] == "Credenciales incorrectas"
    assert not mock_db_session.committed # Check commit was not called

def test_login_user_not_found(mock_db_session):
    # Arrange
    # MockDB is empty by default, so no user will be found
    login_request = MagicMock()
    login_request.email = 'nonexistent@example.com'
    login_request.password = 'password123'

    # Act
    response_obj = login(login_request, mock_db_session)
    response = orjson.loads(response_obj.body)

    # Assert
    assert response["status"] == "error"
    assert response["message"] == "Credenciales incorrectas"
    assert not mock_db_session.committed

@patch('use_cases.login_use_case.verify_password', return_value=True)
@patch('use_cases.login_use_case.send_email')
@patch('use_cases.login_use_case.generate_verification_token', return_value='new_token')
@patch('use_cases.login_use_case.get_user_state')
def test_login_email_not_verified(mock_get_user_state, mock_generate_token, mock_send_email, mock_verify_password, mock_db_session):
    # Arrange
    # Get the "No Verificado" state from the mock database 
    unverified_state = mock_db_session.query(UserStates).filter(lambda s: s.name == 'No Verificado').first()
    
    unverified_user_data = Users(
        user_id=1,
        email='unverified@example.com',
        password_hash='hashed_password',
        name='Unverified User',
        user_state_id=unverified_state.user_state_id, # Use actual ID from database
        verification_token='old_token' # Initial token
    )
    mock_db_session.add(unverified_user_data)

    # get_user_state("Verificado") should return the 'Verificado' state object from MockDB
    verified_user_state_from_db = mock_db_session.query(UserStates).filter(lambda s: s.name == "Verificado").first()
    # get_user_state(ANY OTHER STATE) can return None or the actual state if needed for other logic paths
    # For this test, we only care about the call for "Verificado"
    mock_get_user_state.side_effect = lambda db, state_name: verified_user_state_from_db if state_name == "Verificado" else None

    # The login use case will fetch the user, then its state. 
    # We need to ensure the user object fetched by the use case has a `user_state` attribute or similar
    # that the use case can then use for `user.user_state_id`. 
    # MockDB's User model doesn't automatically link `user_state_id` to a state object.
    # The `login` use case itself likely does `db.query(UserStates).filter(UserStates.user_state_id == user.user_state_id).first()`
    # or uses `get_user_state(user.user_state_id)`. The `get_user_state` patch handles this for "Verificado".
    # For the user's *actual* current state, if the use case fetches it like `user.user_state`, that needs to be mocked or handled.
    # However, the critical check in the login use case is `user.user_state_id != verified_user_state.user_state_id`.
    # As long as `verified_user_state` is correctly returned by `get_user_state("Verificado")` and `user.user_state_id` is set, this logic should work.

    login_request = MagicMock()
    login_request.email = 'unverified@example.com'
    login_request.password = 'password123'

    # Act
    response_obj = login(login_request, mock_db_session)
    response = orjson.loads(response_obj.body)

    # Assert
    assert response["status"] == "error"
    assert response["message"] == "Debes verificar tu correo antes de iniciar sesión"
    
    # Verify the user's token was updated in the mock DB
    updated_user = mock_db_session.query(Users).filter(lambda u: u.email == 'unverified@example.com').first()
    assert updated_user.verification_token == 'new_token'
    
    mock_send_email.assert_called_once_with('unverified@example.com', 'new_token', 'verification')
    assert mock_db_session.committed # Commit should be called to save the new token

@patch('use_cases.login_use_case.verify_password', return_value=True)
@patch('use_cases.login_use_case.send_email')
@patch('use_cases.login_use_case.generate_verification_token', return_value='new_token')
@patch('use_cases.login_use_case.get_user_state', return_value=None) # Simulate 'Verificado' state not found by get_user_state
def test_login_verified_state_not_found(mock_get_user_state_returns_none, mock_generate_token, mock_send_email, mock_verify_password, mock_db_session):
    # Arrange
    # Get any state from the mock database (actual state doesn't matter since get_user_state("Verificado") will return None)
    any_state = mock_db_session.query(UserStates).first()
    
    user_data = Users(
        user_id=1,
        email='test@example.com',
        password_hash='hashed_password',
        name='Test User',
        user_state_id=any_state.user_state_id, # Could be any state, outcome is dictated by get_user_state mock
        verification_token='old_token'
    )
    mock_db_session.add(user_data)

    login_request = MagicMock()
    login_request.email = 'test@example.com'
    login_request.password = 'password123'

    # Act
    response_obj = login(login_request, mock_db_session)
    response = orjson.loads(response_obj.body)

    # Assert
    # Same behavior as email not verified: new token, email sent, commit for token update
    assert response["status"] == "error"
    assert response["message"] == "Debes verificar tu correo antes de iniciar sesión"
    
    updated_user = mock_db_session.query(Users).filter(lambda u: u.email == 'test@example.com').first()
    assert updated_user.verification_token == 'new_token'

    mock_send_email.assert_called_once_with('test@example.com', 'new_token', 'verification')
    assert mock_db_session.committed

@patch('use_cases.login_use_case.verify_password', return_value=True)
@patch('use_cases.login_use_case.send_email', side_effect=Exception("Email send failed"))
@patch('use_cases.login_use_case.generate_verification_token', return_value='new_token')
@patch('use_cases.login_use_case.get_user_state')
def test_login_email_not_verified_send_fail(mock_get_user_state, mock_generate_token, mock_send_email_fails, mock_verify_password, mock_db_session):
    # Arrange
    # Get the "No Verificado" state from the mock database 
    unverified_state = mock_db_session.query(UserStates).filter(lambda s: s.name == 'No Verificado').first()
    
    unverified_user_data = Users(
        user_id=1,
        email='unverified@example.com',
        password_hash='hashed_password',
        name='Unverified User',
        user_state_id=unverified_state.user_state_id, # Use actual ID from database
        verification_token='old_token'
    )
    mock_db_session.add(unverified_user_data)

    # get_user_state("Verificado") should return the 'Verificado' state object
    verified_user_state_from_db = mock_db_session.query(UserStates).filter(lambda s: s.name == "Verificado").first()
    mock_get_user_state.return_value = verified_user_state_from_db 
    # This setup ensures user.user_state_id (unverified) != verified_user_state.user_state_id (verified)

    login_request = MagicMock()
    login_request.email = 'unverified@example.com'
    login_request.password = 'password123'

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        login(login_request, mock_db_session)
    
    assert exc_info.value.status_code == 500
    assert "Error al enviar el nuevo correo de verificación" in str(exc_info.value.detail)
    
    # Token should still be set on the user object in the mock DB
    updated_user = mock_db_session.query(Users).filter(lambda u: u.email == 'unverified@example.com').first()
    assert updated_user.verification_token == 'new_token' 
    
    mock_send_email_fails.assert_called_once_with('unverified@example.com', 'new_token', 'verification')
    # The use case calls commit() before send_email(), then rollback() if send_email() fails.
    assert mock_db_session.committed # Commit was called before the exception
    assert mock_db_session.rolled_back # Rollback was called after the exception

@patch('use_cases.login_use_case.verify_password', return_value=True)
@patch('use_cases.login_use_case.generate_verification_token', return_value='test_session_token')
@patch('use_cases.login_use_case.get_user_state')
def test_login_success_db_error_on_session(mock_get_user_state, mock_generate_token, mock_verify_password, mock_db_session):
    # Arrange
    # Get the "Verificado" state from the mock database 
    verified_state = mock_db_session.query(UserStates).filter(lambda s: s.name == 'Verificado').first()
    
    user_data = Users(
        user_id=1,
        email='test@example.com',
        password_hash='hashed_password',
        name='Test User',
        user_state_id=verified_state.user_state_id, # Use actual ID from database
        verification_token=None
    )
    mock_db_session.add(user_data)

    verified_user_state_from_db = mock_db_session.query(UserStates).filter(lambda s: s.name == "Verificado").first()
    mock_get_user_state.return_value = verified_user_state_from_db

    # Simulate DB error during commit
    # To do this with MockDB, we can patch its commit method for this specific test
    original_commit = mock_db_session.commit 
    def commit_side_effect():
        # Ensure original_commit is called to set mock_db_session.committed = True before raising error
        original_commit() 
        raise OperationalError("DB commit failed", None, None)
    
    mock_db_session.commit = MagicMock(side_effect=commit_side_effect, name="mock_commit_that_fails")
    # We also need to ensure rollback can be called and tracked
    mock_db_session.rollback = MagicMock(name="mock_rollback")

    login_request = MagicMock()
    login_request.email = 'test@example.com'
    login_request.password = 'password123'
    login_request.fcm_token = 'test_fcm_token' # Include FCM token to test that path

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        login(login_request, mock_db_session)
    
    assert exc_info.value.status_code == 500
    assert "Error durante el inicio de sesión" in str(exc_info.value.detail)
    
    # Check that add was called (MockDB doesn't track calls to add directly in a list like MagicMock)
    # We can infer add was called by checking if the device exists, as commit is mocked to fail after adding
    # Or, more directly, the use case should attempt to add UserDevices and UserSessions
    # The login use case adds a UserSession and a UserDevice (if fcm_token is present)
    # We can check the contents of mock_db_session.user_devices and mock_db_session.user_sessions before commit fails.
    # This requires UserSessions to be defined in MockDB and login_use_case to use it.
    # For now, let's assume the critical part is commit and rollback behavior.

    mock_db_session.commit.assert_called_once() # The failing commit was called
    mock_db_session.rollback.assert_called_once() # Rollback was called due to the exception

    # Restore original commit if necessary for other tests or cleanup, though pytest fixtures usually isolate this.
    # mock_db_session.commit = original_commit # Usually not needed due to fixture scoping
