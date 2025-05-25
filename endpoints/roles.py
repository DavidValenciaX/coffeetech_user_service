from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from dataBase import get_db_session
from domain.services import RoleService

router = APIRouter()

@router.get("/list-roles")
def list_roles_endpoint(db: Session = Depends(get_db_session)):
    """
    Retrieves a list of all available roles and their associated permissions.

    Returns a dictionary containing the list of roles, each with its ID, name,
    and a list of permissions associated with that role.
    """
    role_service = RoleService(db)
    return role_service.list_roles_with_permissions()