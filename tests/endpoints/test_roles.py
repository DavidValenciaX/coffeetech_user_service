import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

from endpoints.roles import router
from dataBase import get_db_session
from tests.mockdb import MockDB


# Mock de la función get_db_session
@pytest.fixture
def mock_db_session():
    mock_session = MockDB()
    return mock_session

@pytest.fixture
def client(mock_db_session):
    app = FastAPI()
    # Correct way to override the dependency
    app.dependency_overrides[get_db_session] = lambda: mock_db_session
    app.include_router(router)
    return TestClient(app)

def test_list_roles(client):
    response = client.get("/list-roles")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["message"] == "Roles obtenidos correctamente"
    assert isinstance(data["data"], list)
    assert len(data["data"]) == 3
    assert data["data"][0]["name"] == "Propietario"
    assert data["data"][1]["name"] == "Administrador de finca"
    assert data["data"][2]["name"] == "Operador de campo"
    assert len(data["data"][0]["permissions"]) == 18
    assert len(data["data"][1]["permissions"]) == 13
    assert len(data["data"][2]["permissions"]) == 4
