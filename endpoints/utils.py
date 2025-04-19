from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from models.models import Role
from dataBase import get_db_session

router = APIRouter()

@router.get("/list-roles", summary="Obtener lista de roles", description="Obtiene una lista de todos los roles disponibles junto con sus permisos asociados.")
def list_roles(db: Session = Depends(get_db_session)):
    """
    Obtiene una lista de todos los roles disponibles junto con sus permisos asociados.

    Args:
        db (Session): Sesión de base de datos proporcionada por la dependencia.

    Returns:
        dict: Diccionario con el estado, mensaje y datos de los roles y sus permisos.
    """
    # Consulta los roles y carga los permisos asociados
    roles = db.query(Role).all()

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
