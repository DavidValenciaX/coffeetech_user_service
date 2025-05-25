from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from models.models import Roles, UserRole, Users, UserDevices
from dataBase import get_db_session
from domain.services.session_token_service import verify_session_token
from utils.response import create_response
from domain.schemas import (
    UserRoleCreateRequest,
    BulkUserRoleInfoRequest,
    TokenVerificationRequest,
    UserResponse,
    UserVerificationByEmailRequest,
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/user-role-ids/{user_id}", include_in_schema=False)
def get_user_role_ids(user_id: int, db: Session = Depends(get_db_session)):
    """
    Devuelve una lista de user_role_id asociados a un usuario.
    """
    user_roles = db.query(UserRole).filter(UserRole.user_id == user_id).all()
    user_role_ids = [ur.user_role_id for ur in user_roles]
    return {"user_role_ids": user_role_ids}

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
        raise HTTPException(status_code=404, detail=f"UserRole con ID {user_role_id} no encontrado")
    role = db.query(Roles).filter(Roles.role_id == user_role.role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail=f"Role con ID {user_role.role_id} no encontrado")
    permissions = [
        {
            "permission_id": perm.permission.permission_id,
            "name": perm.permission.name,
            "description": perm.permission.description
        } for perm in role.permissions
    ]
    return {"permissions": permissions}

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

@router.get("/{role_id}/name", include_in_schema=False)
def get_role_name_by_id(role_id: int, db: Session = Depends(get_db_session)):
    """
    Devuelve el nombre de un rol dado su ID.
    """
    role = db.query(Roles).filter(Roles.role_id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail=f"Rol con ID {role_id} no encontrado")
    return {"role_name": role.name}

@router.post("/user-role/{user_role_id}/update-role", include_in_schema=False)
def update_user_role(user_role_id: int, body: dict = Body(...), db: Session = Depends(get_db_session)):
    """
    Actualiza el rol asociado a un user_role_id usando el ID del nuevo rol.
    """
    new_role_id = body.get("new_role_id")
    if not new_role_id:
        raise HTTPException(status_code=400, detail="El ID del nuevo rol es requerido")
    
    # Verificar si el user_role existe
    user_role = db.query(UserRole).filter(UserRole.user_role_id == user_role_id).first()
    if not user_role:
        raise HTTPException(status_code=404, detail=f"UserRole con ID {user_role_id} no encontrado")
    
    # Verificar si el nuevo rol existe
    role = db.query(Roles).filter(Roles.role_id == new_role_id).first()
    if not role:
        raise HTTPException(status_code=400, detail=f"Rol con ID {new_role_id} no encontrado")
    
    # Actualizar el role_id
    user_role.role_id = role.role_id
    db.commit()
    db.refresh(user_role)
    
    # Devolver el nombre del rol actualizado para la respuesta
    return {"status": "success", "message": f"Rol actualizado a '{role.name}'"}

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

@router.post("/session-token-verification", include_in_schema=False)
def verify_token(request: TokenVerificationRequest, db: Session = Depends(get_db_session)):
    """
    Verifica si un token de sesión es válido y devuelve información básica del usuario.
    
    **Parámetros**:
    - **request**: Objeto que contiene el token de sesión a verificar.
    - **db**: Sesión de base de datos, se obtiene automáticamente.
    
    **Respuestas**:
    - **200 OK**: Token válido, se devuelve información del usuario.
    - **401 Unauthorized**: Token inválido o no encontrado.
    """
    user = verify_session_token(request.session_token, db)
    if not user:
        logger.warning("Token de sesión inválido o usuario no encontrado")
        return create_response("error", "Token de sesión inválido o usuario no encontrado", status_code=401)
    
    return create_response("success", "Token de sesión válido", {
        "user": UserResponse(
            user_id=user.user_id,
            name=user.name,
            email=user.email
        )
    })

@router.post("/user-verification-by-email", include_in_schema=False)
def user_verification_by_email(request: UserVerificationByEmailRequest, db: Session = Depends(get_db_session)):
    """
    Verifica si existe un usuario con el email dado.
    Retorna el objeto usuario si existe, None si no.
    """
    try:
        user = db.query(Users).filter(Users.email == request.email).first()
        if user:
            return {
                "status": "success",
                "data": {
                    "user": {
                        "user_id": user.user_id,
                        "name": user.name,
                        "email": user.email
                    }
                }
            }
        else:
            return {
                "status": "error",
                "message": "Usuario no encontrado"
            }
    except SQLAlchemyError as e:
        logger.error(f"Error al verificar usuario por email: {str(e)}")
        return {
            "status": "error",
            "message": "Error interno al consultar el usuario"
        }

@router.get("/user/{user_id}", include_in_schema=False)
def get_user_by_id(user_id: int, db: Session = Depends(get_db_session)):
    """
    Retrieves user information by user ID.
    
    Args:
        user_id: ID of the user to retrieve
        db: Database session
        
    Returns:
        User information if found
    """
    try:
        user = db.query(Users).filter(Users.user_id == user_id).first()
        if not user:
            logger.warning(f"Usuario con ID {user_id} no encontrado")
            return create_response("error", "Usuario no encontrado", status_code=404)
        
        return create_response("success", "Usuario encontrado", data={
            "user": {
                "user_id": user.user_id,
                "name": user.name,
                "email": user.email
            }
        })
    except SQLAlchemyError as e:
        logger.error(f"Error al consultar usuario por ID: {str(e)}")
        return create_response("error", "Error interno al consultar el usuario", status_code=500)

@router.get("/users/{user_id}/devices", include_in_schema=False)
def get_user_devices_by_id(user_id: int, db: Session = Depends(get_db_session)):
    """
    Retrieve all devices associated with a user ID
    
    Args:
        user_id (int): The ID of the user whose devices to retrieve
        db (Session): Database session
        
    Returns:
        List of device objects with user_device_id, user_id, and fcm_token
    """
    try:
        devices = db.query(UserDevices).filter(UserDevices.user_id == user_id).all()
        device_list = [
            {
                "user_device_id": device.user_device_id,
                "user_id": device.user_id,
                "fcm_token": device.fcm_token
            }
            for device in devices
        ]
        return create_response("success", f"Found {len(device_list)} devices", data=device_list)
    except SQLAlchemyError as e:
        logger.error(f"Error retrieving devices for user {user_id}: {str(e)}")
        return create_response("error", "Error al obtener dispositivos del usuario", status_code=500)
