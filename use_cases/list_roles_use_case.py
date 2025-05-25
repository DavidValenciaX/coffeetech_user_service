from fastapi import HTTPException
from domain.repositories import RoleRepository
import logging

logger = logging.getLogger(__name__)

class ListRolesUseCase:
    """
    Caso de uso para listar todos los roles y sus permisos asociados.
    """
    def __init__(self, db):
        self.role_repository = RoleRepository(db)

    def execute(self):
        try:
            logger.info("Iniciando consulta de roles y permisos")
            roles = self.role_repository.list_roles_with_permissions()
            logger.info(f"Se encontraron {len(roles)} roles")

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