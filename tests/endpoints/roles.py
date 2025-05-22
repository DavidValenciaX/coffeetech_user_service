import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from fastapi import FastAPI

from endpoints.roles import router
from dataBase import get_db_session
from models.models import RolePermission, Roles, Permissions


# Mock de la función get_db_session
@pytest.fixture
def mock_db_session():
    # Crear permisos realistas
    permissions = {}
    
    permission_data = [
        (1, 'edit_farm', 'Permite al usuario modificar la informacion de la finca'),
        (2, 'delete_farm', 'Permite al usuario eliminar finca de donde es propietario'),
        (3, 'add_administrator_farm', 'Permite al usuario agregar administrador de finca'),
        (4, 'edit_administrator_farm', 'Permite al usuario editar un rol de colaborador a administrador de finca'),
        (5, 'delete_administrator_farm', 'Permite al usuario eliminar administrador de finca'),
        (6, 'add_operator_farm', 'Permite al usuario agregar operador de campo'),
        (7, 'edit_operator_farm', 'Permite al usuario editar un rol de colaborador a operador de campo'),
        (8, 'delete_operator_farm', 'Permite al usuario eliminar operador de campo'),
        (9, 'read_collaborators', 'Permite al usuario listar los colaboradores de una finca'),
        (10, 'add_plot', 'Permite al usuario agregar lotes'),
        (11, 'edit_plot', 'Permiso para editar lotes'),
        (12, 'delete_plot', 'Permiso para eliminar lotes'),
        (13, 'read_plots', 'Permite al usuario listar los lotes'),
        (14, 'read_transaction', 'Permite al usuario ver las transaciones de la finca'),
        (15, 'edit_transaction', 'Permite al usuario editar las transaciones de la finca'),
        (16, 'add_transaction', 'Permite al usuario agregar las transaciones de la finca'),
        (17, 'delete_transaction', 'Permite al usuario eliminar las transaciones de la finca'),
        (18, 'read_financial_report', 'Permite al usuario ver los reportes financieros')
    ]

    for pid, name, desc in permission_data:
        p = Permissions()
        p.permission_id = pid
        p.name = name
        p.description = desc
        permissions[pid] = p

    # Crear role_permissions
    role_permissions_map = {
        1: [permissions[i] for i in range(1, 19)],  # Propietario
        2: [permissions[i] for i in [1, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17]],  # Administrador de finca
        3: [permissions[i] for i in [9, 13, 14, 16]]  # Operador de campo
    }
    
    # Crear roles
    roles_data = [
        (1, "Propietario"),
        (2, "Administrador de finca"),
        (3, "Operador de campo")
    ]

    roles = []
    for role_id, name in roles_data:
        r = Roles()
        r.role_id = role_id
        r.name = name
        r.permissions = []
        if role_id in role_permissions_map:
            for perm_obj in role_permissions_map[role_id]:
                rp = RolePermission()
                rp.permission = perm_obj
                rp.role_id = role_id
                rp.permission_id = perm_obj.permission_id
                r.permissions.append(rp)
        roles.append(r)
    
    mock_session = MagicMock(spec=Session)
    mock_session.query(Roles).all.return_value = roles
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
