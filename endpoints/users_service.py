from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from dataBase import get_db_session
from domain.services.user_role_service import UserRoleService
from domain.services.user_verification_service import UserVerificationService
from domain.services.user_device_service import UserDeviceService
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

INTERNAL_SERVER_ERROR_MSG = "Error interno del servidor"

@router.get("/user-role-ids/{user_id}", include_in_schema=False)
def get_user_role_ids(user_id: int, db: Session = Depends(get_db_session)):
    """
    Devuelve una lista de user_role_id asociados a un usuario.
    """
    try:
        service = UserRoleService(db)
        user_role_ids = service.get_user_role_ids(user_id)
        return {"user_role_ids": user_role_ids}
    except Exception as e:
        logger.error(f"Error in get_user_role_ids: {str(e)}")
        raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR_MSG)

@router.post("/user-role", status_code=201, include_in_schema=False)
def create_user_role(request: UserRoleCreateRequest, db: Session = Depends(get_db_session)):
    """
    Crea la relación UserRole (usuario-rol) y retorna el id.
    """
    try:
        service = UserRoleService(db)
        user_role_id = service.create_user_role(request.user_id, request.role_name)
        return {"user_role_id": user_role_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in create_user_role: {str(e)}")
        raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR_MSG)

@router.get("/user-role/{user_role_id}", include_in_schema=False)
def get_user_role(user_role_id: int, db: Session = Depends(get_db_session)):
    """
    Get role information for a specific UserRole by ID
    """
    try:
        service = UserRoleService(db)
        user_role_info = service.get_user_role_info(user_role_id)
        return user_role_info
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in get_user_role: {str(e)}")
        raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR_MSG)

@router.get("/user-role/{user_role_id}/permissions", include_in_schema=False)
def get_user_role_permissions(user_role_id: int, db: Session = Depends(get_db_session)):
    """
    Devuelve la lista de permisos (name, description, permission_id) asociados a un user_role_id.
    """
    try:
        service = UserRoleService(db)
        permissions = service.get_user_role_permissions(user_role_id)
        return {"permissions": permissions}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in get_user_role_permissions: {str(e)}")
        raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR_MSG)

@router.post("/user-role/bulk-info", include_in_schema=False)
def bulk_user_role_info(request: BulkUserRoleInfoRequest, db: Session = Depends(get_db_session)):
    """
    Devuelve información de usuario y rol para una lista de user_role_ids.
    """
    try:
        service = UserRoleService(db)
        collaborators = service.get_bulk_user_role_info(request.user_role_ids)
        return {"collaborators": collaborators}
    except Exception as e:
        logger.error(f"Error in bulk_user_role_info: {str(e)}")
        raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR_MSG)

@router.get("/{role_id}/name", include_in_schema=False)
def get_role_name_by_id(role_id: int, db: Session = Depends(get_db_session)):
    """
    Devuelve el nombre de un rol dado su ID.
    """
    try:
        service = UserRoleService(db)
        role_name = service.get_role_name_by_id(role_id)
        return {"role_name": role_name}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in get_role_name_by_id: {str(e)}")
        raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR_MSG)

@router.post("/user-role/{user_role_id}/update-role", include_in_schema=False)
def update_user_role(user_role_id: int, body: dict = Body(...), db: Session = Depends(get_db_session)):
    """
    Actualiza el rol asociado a un user_role_id usando el ID del nuevo rol.
    """
    new_role_id = body.get("new_role_id")
    if not new_role_id:
        raise HTTPException(status_code=400, detail="El ID del nuevo rol es requerido")
    
    try:
        service = UserRoleService(db)
        role_name = service.update_user_role(user_role_id, new_role_id)
        return {"status": "success", "message": f"Rol actualizado a '{role_name}'"}
    except ValueError as e:
        # Determinar el código de error apropiado basado en el mensaje
        if "UserRole" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in update_user_role: {str(e)}")
        raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR_MSG)

@router.post("/user-role/{user_role_id}/delete", include_in_schema=False)
def delete_user_role(user_role_id: int, db: Session = Depends(get_db_session)):
    """
    Elimina la relación UserRole (usuario-rol) especificada por user_role_id.
    """
    try:
        service = UserRoleService(db)
        service.delete_user_role(user_role_id)
        return {"status": "success", "message": f"UserRole con ID {user_role_id} eliminado correctamente"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in delete_user_role: {str(e)}")
        raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR_MSG)

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
    try:
        service = UserVerificationService(db)
        user = service.verify_session_token(request.session_token)
        
        return create_response("success", "Token de sesión válido", {
            "user": UserResponse(
                user_id=user.user_id,
                name=user.name,
                email=user.email
            )
        })
    except ValueError as e:
        logger.warning(f"Token verification failed: {str(e)}")
        return create_response("error", str(e), status_code=401)
    except Exception as e:
        logger.error(f"Error in verify_token: {str(e)}")
        return create_response("error", INTERNAL_SERVER_ERROR_MSG, status_code=500)

@router.post("/user-verification-by-email", include_in_schema=False)
def user_verification_by_email(request: UserVerificationByEmailRequest, db: Session = Depends(get_db_session)):
    """
    Verifica si existe un usuario con el email dado.
    Retorna el objeto usuario si existe, None si no.
    """
    try:
        service = UserVerificationService(db)
        user_data = service.verify_user_by_email(request.email)
        
        if user_data:
            return {
                "status": "success",
                "data": {
                    "user": user_data
                }
            }
        else:
            return {
                "status": "error",
                "message": "Usuario no encontrado"
            }
    except Exception as e:
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
        service = UserVerificationService(db)
        user_data = service.get_user_by_id(user_id)
        
        if not user_data:
            logger.warning(f"Usuario con ID {user_id} no encontrado")
            return create_response("error", "Usuario no encontrado", status_code=404)
        
        return create_response("success", "Usuario encontrado", data={
            "user": user_data
        })
    except Exception as e:
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
        service = UserDeviceService(db)
        device_list = service.get_user_devices(user_id)
        return create_response("success", f"Found {len(device_list)} devices", data=device_list)
    except Exception as e:
        logger.error(f"Error retrieving devices for user {user_id}: {str(e)}")
        return create_response("error", "Error al obtener dispositivos del usuario", status_code=500)
