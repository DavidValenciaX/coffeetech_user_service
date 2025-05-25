import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException
from use_cases.list_roles_use_case import ListRolesUseCase


class TestListRolesUseCase:
    """Test cases for the list_roles use case"""

    def test_list_roles_success(self):
        """Test successful listing of roles with permissions"""
        # Arrange
        mock_db = MagicMock()
        
        # Mock permission objects
        mock_permission1 = MagicMock()
        mock_permission1.permission_id = 1
        mock_permission1.name = "read_users"
        mock_permission1.description = "Read users permission"
        
        mock_permission2 = MagicMock()
        mock_permission2.permission_id = 2
        mock_permission2.name = "write_users"
        mock_permission2.description = "Write users permission"
        
        # Mock role permission objects
        mock_role_perm1 = MagicMock()
        mock_role_perm1.permission = mock_permission1
        
        mock_role_perm2 = MagicMock()
        mock_role_perm2.permission = mock_permission2
        
        # Mock role objects
        mock_role1 = MagicMock()
        mock_role1.role_id = 1
        mock_role1.name = "Admin"
        mock_role1.permissions = [mock_role_perm1, mock_role_perm2]
        
        mock_role2 = MagicMock()
        mock_role2.role_id = 2
        mock_role2.name = "User"
        mock_role2.permissions = [mock_role_perm1]
        
        mock_db.query().all.return_value = [mock_role1, mock_role2]
        
        # Act
        result = ListRolesUseCase(mock_db).execute()
        
        # Assert
        assert result["status"] == "success"
        assert result["message"] == "Roles obtenidos correctamente"
        assert len(result["data"]) == 2
        
        # Check first role
        assert result["data"][0]["role_id"] == 1
        assert result["data"][0]["name"] == "Admin"
        assert len(result["data"][0]["permissions"]) == 2
        assert result["data"][0]["permissions"][0]["permission_id"] == 1
        assert result["data"][0]["permissions"][0]["name"] == "read_users"
        
        # Check second role
        assert result["data"][1]["role_id"] == 2
        assert result["data"][1]["name"] == "User"
        assert len(result["data"][1]["permissions"]) == 1

    def test_list_roles_empty_result(self):
        """Test listing roles when no roles exist"""
        # Arrange
        mock_db = MagicMock()
        mock_db.query().all.return_value = []
        
        # Act
        result = ListRolesUseCase(mock_db).execute()
        
        # Assert
        assert result["status"] == "success"
        assert result["message"] == "Roles obtenidos correctamente"
        assert result["data"] == []

    def test_list_roles_database_error(self):
        """Test database error handling"""
        # Arrange
        mock_db = MagicMock()
        mock_db.query().all.side_effect = Exception("Database connection error")
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            ListRolesUseCase(mock_db).execute()
        
        assert exc_info.value.status_code == 500
        assert "Error al obtener los roles" in str(exc_info.value.detail)

    def test_list_roles_role_without_permissions(self):
        """Test listing roles where a role has no permissions"""
        # Arrange
        mock_db = MagicMock()
        
        mock_role = MagicMock()
        mock_role.role_id = 1
        mock_role.name = "Empty Role"
        mock_role.permissions = []
        
        mock_db.query().all.return_value = [mock_role]
        
        # Act
        result = ListRolesUseCase(mock_db).execute()
        
        # Assert
        assert result["status"] == "success"
        assert result["message"] == "Roles obtenidos correctamente"
        assert len(result["data"]) == 1
        assert result["data"][0]["role_id"] == 1
        assert result["data"][0]["name"] == "Empty Role"
        assert result["data"][0]["permissions"] == [] 