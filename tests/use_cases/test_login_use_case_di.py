import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import pytest
from unittest.mock import MagicMock
import orjson

from use_cases.login_use_case_di import LoginUseCase
from tests.mockdb import MockDB, Users, UserStates

class MockPasswordVerifier:
    def __init__(self, should_verify=True):
        self.should_verify = should_verify
    
    def verify(self, password, hash):
        return self.should_verify

class MockTokenGenerator:
    def __init__(self, token='test_token'):
        self.token = token
    
    def generate(self, length):
        return self.token

class MockEmailSender:
    def __init__(self, should_fail=False):
        self.should_fail = should_fail
        self.sent_emails = []
    
    def send(self, email, token, type):
        if self.should_fail:
            raise Exception("Email send failed")
        self.sent_emails.append((email, token, type))

class MockStateService:
    def __init__(self, state_to_return=None):
        self.state_to_return = state_to_return
    
    def get_user_state(self, db, state_name):
        return self.state_to_return

@pytest.fixture
def mock_db_session():
    return MockDB()

def test_login_success_with_di(mock_db_session):
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

    # Create mocks with clear behavior
    password_verifier = MockPasswordVerifier(should_verify=True)
    token_generator = MockTokenGenerator('test_session_token')
    email_sender = MockEmailSender()
    state_service = MockStateService(verified_state)

    # Create use case with injected dependencies
    login_use_case = LoginUseCase(password_verifier, token_generator, email_sender, state_service)

    login_request = MagicMock()
    login_request.email = 'test@example.com'
    login_request.password = 'password123'
    login_request.fcm_token = 'test_fcm_token'

    # Act
    response_obj = login_use_case.execute(login_request, mock_db_session)
    response = orjson.loads(response_obj.body)

    # Assert
    assert response["status"] == "success"
    assert response["message"] == "Inicio de sesión exitoso"
    assert response["data"]["session_token"] == "test_session_token"
    assert response["data"]["name"] == "Test User"
    assert mock_db_session.committed

def test_login_incorrect_credentials_with_di(mock_db_session):
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

    # Mock to return False for password verification
    password_verifier = MockPasswordVerifier(should_verify=False)
    token_generator = MockTokenGenerator()
    email_sender = MockEmailSender()
    state_service = MockStateService(verified_state)

    login_use_case = LoginUseCase(password_verifier, token_generator, email_sender, state_service)

    login_request = MagicMock()
    login_request.email = 'test@example.com'
    login_request.password = 'wrong_password'

    # Act
    response_obj = login_use_case.execute(login_request, mock_db_session)
    response = orjson.loads(response_obj.body)

    # Assert
    assert response["status"] == "error"
    assert response["message"] == "Credenciales incorrectas"
    assert not mock_db_session.committed

def test_login_email_not_verified_with_di(mock_db_session):
    # Arrange
    unverified_state = mock_db_session.query(UserStates).filter(lambda s: s.name == 'No Verificado').first()
    verified_state = mock_db_session.query(UserStates).filter(lambda s: s.name == 'Verificado').first()
    
    user_data = Users(
        user_id=1,
        email='unverified@example.com',
        password_hash='hashed_password',
        name='Unverified User',
        user_state_id=unverified_state.user_state_id,
        verification_token='old_token'
    )
    mock_db_session.add(user_data)

    password_verifier = MockPasswordVerifier(should_verify=True)
    token_generator = MockTokenGenerator('new_token')
    email_sender = MockEmailSender()
    state_service = MockStateService(verified_state)  # Returns verified state

    login_use_case = LoginUseCase(password_verifier, token_generator, email_sender, state_service)

    login_request = MagicMock()
    login_request.email = 'unverified@example.com'
    login_request.password = 'password123'

    # Act
    response_obj = login_use_case.execute(login_request, mock_db_session)
    response = orjson.loads(response_obj.body)

    # Assert
    assert response["status"] == "error"
    assert response["message"] == "Debes verificar tu correo antes de iniciar sesión"
    
    # Verify email was sent
    assert len(email_sender.sent_emails) == 1
    assert email_sender.sent_emails[0] == ('unverified@example.com', 'new_token', 'verification')
    
    # Verify token was updated
    updated_user = mock_db_session.query(Users).filter(lambda u: u.email == 'unverified@example.com').first()
    assert updated_user.verification_token == 'new_token'
    assert mock_db_session.committed 