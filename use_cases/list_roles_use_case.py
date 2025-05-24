from fastapi import HTTPException
from models.models import Roles
import logging

logger = logging.getLogger(__name__)

def list_roles(db):
    """
    Lista todos los roles disponibles y sus permisos asociados.
    
    Args:
        db: Sesión de base de datos SQLAlchemy
        
    Returns:
        dict: Respuesta estándar con la lista de roles y sus permisos
        
    Raises:
        HTTPException: En caso de error al consultar la base de datos
    """
    try:
        logger.info("Iniciando consulta de roles y permisos")
        
        # Consulta los roles y carga los permisos asociados
        roles = db.query(Roles).all()
        
        logger.info(f"Se encontraron {len(roles)} roles")
        
        # Construir los datos de roles con sus permisos
        roles_data = []
        for role in roles:
            role_data = {
                "role_id": role.role_id,
                "name": role.name,
                "permissions": [
                    {
                        "permission_id": perm.permission.permission_id,
                        "name": perm.permission.name,
                        "description": perm.permission.description
                    } for perm in role.permissions
                ]
            }
            roles_data.append(role_data)
        
        logger.info("Consulta de roles completada exitosamente")
        
        return {
            "status": "success",
            "message": "Roles obtenidos correctamente",
            "data": roles_data
        }
        
    except Exception as e:
        logger.error(f"Error al consultar los roles: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error al obtener los roles: {str(e)}"
        ) 