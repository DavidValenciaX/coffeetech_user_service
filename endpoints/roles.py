from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from models.models import Roles, UserRole
from dataBase import get_db_session

router = APIRouter()

@router.get("/list-roles")
def list_roles(db: Session = Depends(get_db_session)):
    """
    Retrieves a list of all available roles and their associated permissions.

    Returns a dictionary containing the list of roles, each with its ID, name,
    and a list of permissions associated with that role.
    """
    # Consulta los roles y carga los permisos asociados
    roles = db.query(Roles).all()

    # Construir la respuesta con roles y sus permisos
    return {
        "status": "success",
        "message": "Roles obtenidos correctamente",
        "data": [
            {
                "role_id": role.role_id,
                "name": role.name,
                "permissions": [
                    {
                        "permission_id": perm.permission.permission_id,
                        "name": perm.permission.name,
                        "description": perm.permission.description
                    } for perm in role.permissions
                ]
            } for role in roles
        ]
    }

@router.get("/user-role-ids/{user_id}", include_in_schema=False)
def get_user_role_ids(user_id: int, db: Session = Depends(get_db_session)):
    """
    Devuelve una lista de user_role_id asociados a un usuario.
    """
    user_roles = db.query(UserRole).filter(UserRole.user_id == user_id).all()
    user_role_ids = [ur.user_role_id for ur in user_roles]
    return {"user_role_ids": user_role_ids}
