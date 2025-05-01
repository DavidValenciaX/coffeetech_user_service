from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from models.models import Roles, UserRole, Roles, Users
from dataBase import get_db_session
from pydantic import BaseModel
from typing import List

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

class UserRoleCreateRequest(BaseModel):
    user_id: int
    role_name: str

@router.post("/user-role", status_code=201, include_in_schema=False)
def create_user_role(request: UserRoleCreateRequest, db: Session = Depends(get_db_session)):
    """
    Crea la relación UserRole (usuario-rol) y retorna el id.
    """
    # Buscar el rol por nombre
    role = db.query(Roles).filter(Roles.name == request.role_name).first()
    if not role:
        raise HTTPException(status_code=400, detail=f"Rol '{request.role_name}' no encontrado")
    # Verificar si ya existe la relación
    user_role = db.query(UserRole).filter(
        UserRole.user_id == request.user_id,
        UserRole.role_id == role.role_id
    ).first()
    if not user_role:
        user_role = UserRole(user_id=request.user_id, role_id=role.role_id)
        db.add(user_role)
        db.commit()
        db.refresh(user_role)
    return {"user_role_id": user_role.user_role_id}

@router.get("/user-role/{user_role_id}", include_in_schema=False)
def get_user_role(user_role_id: int, db: Session = Depends(get_db_session)):
    """
    Get role information for a specific UserRole by ID
    """
    user_role = db.query(UserRole).filter(UserRole.user_role_id == user_role_id).first()
    if not user_role:
        raise HTTPException(status_code=404, detail=f"UserRole with ID {user_role_id} not found")
        
    role = db.query(Roles).filter(Roles.role_id == user_role.role_id).first()
    
    return {
        "user_role_id": user_role.user_role_id,
        "user_id": user_role.user_id,
        "role_id": user_role.role_id,
        "role_name": role.name if role else "Unknown"
    }

@router.get("/user-role/{user_role_id}/permissions", include_in_schema=False)
def get_user_role_permissions(user_role_id: int, db: Session = Depends(get_db_session)):
    """
    Devuelve la lista de permisos (name, description, permission_id) asociados a un user_role_id.
    """
    user_role = db.query(UserRole).filter(UserRole.user_role_id == user_role_id).first()
    if not user_role:
        raise HTTPException(status_code=404, detail=f"UserRole with ID {user_role_id} not found")
    role = db.query(Roles).filter(Roles.role_id == user_role.role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail=f"Role with ID {user_role.role_id} not found")
    permissions = [
        {
            "permission_id": perm.permission.permission_id,
            "name": perm.permission.name,
            "description": perm.permission.description
        } for perm in role.permissions
    ]
    return {"permissions": permissions}

class BulkUserRoleInfoRequest(BaseModel):
    user_role_ids: List[int]

@router.post("/user-role/bulk-info", include_in_schema=False)
def bulk_user_role_info(request: BulkUserRoleInfoRequest, db: Session = Depends(get_db_session)):
    """
    Devuelve información de usuario y rol para una lista de user_role_ids.
    """
    user_roles = db.query(UserRole).filter(UserRole.user_role_id.in_(request.user_role_ids)).all()
    collaborators = []
    for ur in user_roles:
        user = db.query(Users).filter(Users.user_id == ur.user_id).first()
        role = db.query(Roles).filter(Roles.role_id == ur.role_id).first()
        if user and role:
            collaborators.append({
                "user_role_id": ur.user_role_id,
                "user_id": user.user_id,
                "user_name": user.name,
                "user_email": user.email,
                "role_id": role.role_id,
                "role_name": role.name
            })
    return {"collaborators": collaborators}

@router.post("/user-role/{user_role_id}/update-role", include_in_schema=False)
def update_user_role(user_role_id: int, body: dict = Body(...), db: Session = Depends(get_db_session)):
    """
    Actualiza el rol asociado a un user_role_id.
    """
    new_role_name = body.get("new_role_name")
    if not new_role_name:
        raise HTTPException(status_code=400, detail="El nombre del nuevo rol es requerido")
    user_role = db.query(UserRole).filter(UserRole.user_role_id == user_role_id).first()
    if not user_role:
        raise HTTPException(status_code=404, detail=f"UserRole con ID {user_role_id} no encontrado")
    role = db.query(Roles).filter(Roles.name == new_role_name).first()
    if not role:
        raise HTTPException(status_code=400, detail=f"Rol '{new_role_name}' no encontrado")
    user_role.role_id = role.role_id
    db.commit()
    db.refresh(user_role)
    return {"status": "success", "message": f"Rol actualizado a '{new_role_name}'"}

@router.post("/user-role/{user_role_id}/delete", include_in_schema=False)
def delete_user_role(user_role_id: int, db: Session = Depends(get_db_session)):
    """
    Elimina la relación UserRole (usuario-rol) especificada por user_role_id.
    """
    user_role = db.query(UserRole).filter(UserRole.user_role_id == user_role_id).first()
    if not user_role:
        raise HTTPException(status_code=404, detail=f"UserRole con ID {user_role_id} no encontrado")
    db.delete(user_role)
    db.commit()
    return {"status": "success", "message": f"UserRole con ID {user_role_id} eliminado correctamente"}