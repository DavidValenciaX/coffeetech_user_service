import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
import orjson
from sqlalchemy.exc import OperationalError

from use_cases.login_use_case import LoginUseCase
from tests.mockdb import MockDB, UserSessions, Users, UserDevices, UserStates

@pytest.fixture
def mock_db_session():
    # Instantiate MockDB from mockdb.py
    db = MockDB()
    return db

@patch('use_cases.login_use_case.verify_password')
@patch('use_cases.login_use_case.generate_verification_token')
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

    # Configure mocks to return the verified state, generate a token, and verify the password
    mock_get_user_state.return_value = verified_state
    mock_generate_token.return_value = 'test_session_token'
    mock_verify_password.return_value = True
    
    login_request = MagicMock()
    login_request.email = 'test@example.com'
    login_request.password = 'password123'
    login_request.fcm_token = 'test_fcm_token'

    # Act
    use_case = LoginUseCase(mock_db_session)
    response_obj = use_case.execute(login_request)
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

@patch('use_cases.login_use_case.verify_password')
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
    
    # Configure mocks to return verify the password
    mock_verify_password.return_value = False

    login_request = MagicMock()
    login_request.email = 'test@example.com'
    login_request.password = 'wrong_password'

    # Act
    use_case = LoginUseCase(mock_db_session)
    response_obj = use_case.execute(login_request)
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
    use_case = LoginUseCase(mock_db_session)
    response_obj = use_case.execute(login_request)
    response = orjson.loads(response_obj.body)

    # Assert
    assert response["status"] == "error"
    assert response["message"] == "Credenciales incorrectas"
    assert not mock_db_session.committed

@patch('use_cases.login_use_case.verify_password')
@patch('use_cases.login_use_case.send_email')
@patch('use_cases.login_use_case.generate_verification_token')
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
        user_state_id=unverified_state.user_state_id,
        verification_token='old_token' # Initial token
    )
    mock_db_session.add(unverified_user_data)

    # get_user_state("Verificado") should return the 'Verificado' state object from MockDB
    verified_state = mock_db_session.query(UserStates).filter(lambda s: s.name == "Verificado").first()

    # Mock the get_user_state function to return the 'Verificado' state object
    mock_get_user_state.side_effect = lambda db, state_name: verified_state if state_name == "Verificado" else None
    mock_generate_token.return_value = 'new_token'
    mock_verify_password.return_value = True

    login_request = MagicMock()
    login_request.email = 'unverified@example.com'
    login_request.password = 'password123'

    # Act
    use_case = LoginUseCase(mock_db_session)
    response_obj = use_case.execute(login_request)
    response = orjson.loads(response_obj.body)

    # Assert
    assert response["status"] == "error"
    assert response["message"] == "Debes verificar tu correo antes de iniciar sesión"
    
    # Verify the user's token was updated in the mock DB
    updated_user = mock_db_session.query(Users).filter(lambda u: u.email == 'unverified@example.com').first()
    assert updated_user.verification_token == 'new_token'
    
    mock_send_email.assert_called_once_with('unverified@example.com', 'new_token', 'verification')
    assert mock_db_session.committed # Commit should be called to save the new token

@patch('use_cases.login_use_case.verify_password')
@patch('use_cases.login_use_case.send_email')
@patch('use_cases.login_use_case.generate_verification_token')
@patch('use_cases.login_use_case.get_user_state')
def test_login_verified_state_not_found(mock_get_user_state, mock_generate_token, mock_send_email, mock_verify_password, mock_db_session):
    # Arrange
    # Get the "Verificado" state from the mock database
    verified_state = mock_db_session.query(UserStates).filter(lambda s: s.name == 'Verificado').first()
    
    user_data = Users(
        user_id=1,
        email='test@example.com',
        password_hash='hashed_password',
        name='Test User',
        user_state_id=verified_state.user_state_id,
        verification_token='old_token'
    )
    mock_db_session.add(user_data)
    
    # Configure mocks to return None for get_user_state, generate a token, and verify the password
    mock_get_user_state.return_value = None
    mock_generate_token.return_value = 'new_token'
    mock_verify_password.return_value = True

    login_request = MagicMock()
    login_request.email = 'test@example.com'
    login_request.password = 'password123'

    # Act
    use_case = LoginUseCase(mock_db_session)
    response_obj = use_case.execute(login_request)
    response = orjson.loads(response_obj.body)

    # Assert
    assert response["status"] == "error"
    assert response["message"] == "Debes verificar tu correo antes de iniciar sesión"
    
    updated_user = mock_db_session.query(Users).filter(lambda u: u.email == 'test@example.com').first()
    assert updated_user.verification_token == 'new_token'

    mock_send_email.assert_called_once_with('test@example.com', 'new_token', 'verification')
    assert mock_db_session.committed

@patch('use_cases.login_use_case.verify_password')
@patch('use_cases.login_use_case.send_email')
@patch('use_cases.login_use_case.generate_verification_token')
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
        user_state_id=unverified_state.user_state_id,
        verification_token='old_token'
    )
    mock_db_session.add(unverified_user_data)

    verified_state = mock_db_session.query(UserStates).filter(lambda s: s.name == "Verificado").first()
    
    # Configure mocks to return the verified state, generate a token, and verify the password
    mock_get_user_state.return_value = verified_state 
    mock_generate_token.return_value = 'new_token'
    mock_verify_password.return_value = True
    mock_send_email_fails.side_effect = Exception("Email send failed")

    login_request = MagicMock()
    login_request.email = 'unverified@example.com'
    login_request.password = 'password123'

    # Act
    use_case = LoginUseCase(mock_db_session)
    with pytest.raises(HTTPException) as exc_info:
        use_case.execute(login_request)
    
    # Assert
    assert exc_info.value.status_code == 500
    assert "Error al enviar el nuevo correo de verificación" in str(exc_info.value.detail)
    
    # Token should still be set on the user object in the mock DB
    updated_user = mock_db_session.query(Users).filter(lambda u: u.email == 'unverified@example.com').first()
    assert updated_user.verification_token == 'new_token' 
    
    mock_send_email_fails.assert_called_once_with('unverified@example.com', 'new_token', 'verification')
    # The use case calls commit() before send_email(), then rollback() if send_email() fails.
    assert mock_db_session.committed # Commit was called before the exception
    assert mock_db_session.rolled_back # Rollback was called after the exception

@patch('use_cases.login_use_case.verify_password')
@patch('use_cases.login_use_case.generate_verification_token')
@patch('use_cases.login_use_case.get_user_state')
def test_login_success_db_error_on_session(mock_get_user_state, mock_generate_token, mock_verify_password, mock_db_session):
    # Arrange
    verified_state = mock_db_session.query(UserStates).filter(lambda s: s.name == 'Verificado').first()
    
    user_data = Users(
        user_id=1,
        email='test@example.com',
        password_hash='hashed_password',
        name='Test User',
        user_state_id=verified_state.user_state_id,
        verification_token=None
    )
    mock_db_session.add(user_data)

    mock_get_user_state.return_value = verified_state
    mock_generate_token.return_value = 'test_session_token'
    mock_verify_password.return_value = True
    
    # commit fails
    mock_db_session.set_commit_fail(True, "DB commit failed")

    login_request = MagicMock()
    login_request.email = 'test@example.com'
    login_request.password = 'password123'
    login_request.fcm_token = 'test_fcm_token'

    # Act
    use_case = LoginUseCase(mock_db_session)
    with pytest.raises(HTTPException) as exc_info:
        use_case.execute(login_request)
    
    # Assert
    assert exc_info.value.status_code == 500
    assert "Error durante el inicio de sesión" in str(exc_info.value.detail)
    assert mock_db_session.committed
    assert mock_db_session.rolled_back
