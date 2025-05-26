import sys
import os
from sqlalchemy.sql.elements import BinaryExpression

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

class UserStates:
    def __init__(self, user_state_id, name):
        self.user_state_id = user_state_id
        self.name = name

class Users:
    def __init__(self, user_id, name, email, password_hash, verification_token, user_state_id):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.password_hash = password_hash
        self.verification_token = verification_token
        self.user_state_id = user_state_id

class UserSessions:
    def __init__(self, user_session_id=None, user_id=None, session_token=None):
        self.user_session_id = user_session_id
        self.user_id = user_id
        self.session_token = session_token

class UserDevices:
    def __init__(self, user_device_id, user_id, fcm_token):
        self.user_device_id = user_device_id
        self.user_id = user_id
        self.fcm_token = fcm_token

class Roles:
    def __init__(self, role_id, name):
        self.role_id = role_id
        self.name = name
        self.permissions = []

class Permissions:
    def __init__(self, permission_id, name, description):
        self.permission_id = permission_id
        self.name = name
        self.description = description

class RolePermission:
    def __init__(self, role_id, permission_id, permission=None):
        self.role_id = role_id
        self.permission_id = permission_id
        self.permission = permission

class UserRole:
    def __init__(self, user_role_id, user_id, role_id):
        self.user_role_id = user_role_id
        self.user_id = user_id
        self.role_id = role_id

class MockQuery:
    def __init__(self, data, mock_db=None):
        self.data = data
        self._filters = []
        self.mock_db = mock_db

    def filter(self, *args):
        for arg in args:
            if callable(arg):
                # It's a lambda function, use as is
                self._filters.append(arg)
            elif isinstance(arg, BinaryExpression):
                # Convert SQLAlchemy BinaryExpression to a callable function
                filter_func = self._convert_binary_expression_to_function(arg)
                self._filters.append(filter_func)
            else:
                # For other types, try to make them callable
                self._filters.append(lambda obj, condition=arg: condition)
        return self

    def _convert_binary_expression_to_function(self, expr):
        """Convert a SQLAlchemy BinaryExpression to a callable function"""
        left = expr.left
        right = expr.right
        operator = expr.operator
        
        # Get the column name from the left side (e.g., Users.email -> 'email')
        if hasattr(left, 'name'):
            column_name = left.name
        elif hasattr(left, 'key'):
            column_name = left.key
        else:
            # Fallback - try to extract from string representation
            column_name = str(left).split('.')[-1]
        
        # Get the value from the right side
        if hasattr(right, 'value'):
            compare_value = right.value
        else:
            compare_value = right
        
        # Create appropriate comparison function based on operator
        if operator.__name__ == 'eq':  # ==
            return lambda obj: getattr(obj, column_name, None) == compare_value
        elif operator.__name__ == 'ne':  # !=
            return lambda obj: getattr(obj, column_name, None) != compare_value
        elif operator.__name__ == 'lt':  # <
            return lambda obj: getattr(obj, column_name, None) < compare_value
        elif operator.__name__ == 'le':  # <=
            return lambda obj: getattr(obj, column_name, None) <= compare_value
        elif operator.__name__ == 'gt':  # >
            return lambda obj: getattr(obj, column_name, None) > compare_value
        elif operator.__name__ == 'ge':  # >=
            return lambda obj: getattr(obj, column_name, None) >= compare_value
        else:
            # Default to equality comparison
            return lambda obj: getattr(obj, column_name, None) == compare_value

    def all(self):
        result = []
        for obj in self.data:
            if all(f(obj) for f in self._filters):
                result.append(obj)
        return result

    def first(self):
        for obj in self.data:
            if all(f(obj) for f in self._filters):
                return obj
        return None

    def delete(self):
        """Bulk delete all objects matching the current filters"""
        if self.mock_db is None:
            # If we don't have a reference to the mock_db, just return 0
            return 0
        
        # Find all objects matching the filters
        objects_to_delete = []
        for obj in self.data:
            if all(f(obj) for f in self._filters):
                objects_to_delete.append(obj)
        
        # Remove them from the appropriate collections
        for obj in objects_to_delete:
            self.mock_db.delete(obj)
        
        # Return the count of deleted objects
        return len(objects_to_delete)

class MockDB:
    def __init__(self):
        self.users = []
        self.user_states = []
        self.user_sessions = []
        self.user_devices = []
        self.roles = []
        self.permissions = []
        self.role_permissions = []
        self.user_roles = []
        self.committed = False
        self.rolled_back = False
        
        # Agregar configuración para simular fallos
        self.should_commit_fail = False
        self.should_rollback_fail = False
        self.commit_error_message = "DB commit failed"
        self.rollback_error_message = "DB rollback failed"

        # Initialize common user states
        user_states_data = [
            (1, 'Verificado'),
            (2, 'No Verificado'),
            (3, 'Pendiente')
        ]
        
        for state_id, name in user_states_data:
            state = UserStates(user_state_id=state_id, name=name)
            self.user_states.append(state)

        # Data from test_roles.py
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
            p = Permissions(permission_id=pid, name=name, description=desc)
            self.permissions.append(p)

        roles_data = [
            (1, "Propietario"),
            (2, "Administrador de finca"),
            (3, "Operador de campo")
        ]

        # Create role_permissions
        # Mapping role_id to list of permission_ids
        role_permissions_mapping = {
            1: list(range(1, 19)),  # Propietario
            2: [1, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17],  # Administrador de finca
            3: [9, 13, 14, 16]  # Operador de campo
        }
        
        permissions_dict = {p.permission_id: p for p in self.permissions}

        for role_id, name in roles_data:
            r = Roles(role_id=role_id, name=name)
            if role_id in role_permissions_mapping:
                for perm_id in role_permissions_mapping[role_id]:
                    permission_obj = permissions_dict.get(perm_id)
                    if permission_obj:
                        rp = RolePermission(role_id=role_id, permission_id=perm_id, permission=permission_obj)
                        self.role_permissions.append(rp)
                        # Link permission object to role, similar to test_roles.py setup
                        r.permissions.append(rp) 
            self.roles.append(r)

    def query(self, model):
        if model.__name__ == "Users":
            return MockQuery(self.users, self)
        if model.__name__ == "UserStates":
            return MockQuery(self.user_states, self)
        if model.__name__ == "UserSessions":
            return MockQuery(self.user_sessions, self)
        if model.__name__ == "UserDevices":
            return MockQuery(self.user_devices, self)
        if model.__name__ == "Roles":
            return MockQuery(self.roles, self)
        if model.__name__ == "Permissions":
            return MockQuery(self.permissions, self)
        if model.__name__ == "RolePermission":
            return MockQuery(self.role_permissions, self)
        if model.__name__ == "UserRole":
            return MockQuery(self.user_roles, self)
        return MockQuery([])

    def add(self, obj):
        if obj.__class__.__name__ == "Users":
            self.users.append(obj)
        elif obj.__class__.__name__ == "UserStates":
            self.user_states.append(obj)
        elif obj.__class__.__name__ == "UserSessions":
            self.user_sessions.append(obj)
        elif obj.__class__.__name__ == "UserDevices":
            self.user_devices.append(obj)
        elif obj.__class__.__name__ == "Roles":
            self.roles.append(obj)
        elif obj.__class__.__name__ == "Permissions":
            self.permissions.append(obj)
        elif obj.__class__.__name__ == "RolePermission":
            self.role_permissions.append(obj)
        elif obj.__class__.__name__ == "UserRole":
            self.user_roles.append(obj)

    def commit(self):
        if self.should_commit_fail:
            # Marcar como committed antes de fallar (comportamiento real)
            self.committed = True
            from sqlalchemy.exc import OperationalError
            raise OperationalError(self.commit_error_message, None, None)
        self.committed = True

    def rollback(self):
        if self.should_rollback_fail:
            from sqlalchemy.exc import OperationalError
            raise OperationalError(self.rollback_error_message, None, None)
        self.rolled_back = True

    def delete(self, obj):
        """Delete an object from the mock database."""
        model_collections = {
            "Users": self.users,
            "UserStates": self.user_states,
            "UserSessions": self.user_sessions,
            "UserDevices": self.user_devices,
            "Roles": self.roles,
            "Permissions": self.permissions,
            "RolePermission": self.role_permissions,
            "UserRole": self.user_roles
        }
        
        collection = model_collections.get(obj.__class__.__name__)
        if collection is not None and obj in collection:
            collection.remove(obj)
    
    # Métodos de configuración para tests
    def set_commit_fail(self, should_fail=True, error_message="DB commit failed"):
        self.should_commit_fail = should_fail
        self.commit_error_message = error_message
    
    def set_rollback_fail(self, should_fail=True, error_message="DB rollback failed"):
        self.should_rollback_fail = should_fail
        self.rollback_error_message = error_message
    
    def reset_failure_modes(self):
        self.should_commit_fail = False
        self.should_rollback_fail = False