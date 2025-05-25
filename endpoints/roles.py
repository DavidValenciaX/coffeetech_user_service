from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from dataBase import get_db_session
from use_cases.list_roles_use_case import ListRolesUseCase

router = APIRouter()

@router.get("/list-roles")
def list_roles_endpoint(db: Session = Depends(get_db_session)):
    """
    Retrieves a list of all available roles and their associated permissions.

    Returns a dictionary containing the list of roles, each with its ID, name,
    and a list of permissions associated with that role.
    """
    return ListRolesUseCase(db).execute()