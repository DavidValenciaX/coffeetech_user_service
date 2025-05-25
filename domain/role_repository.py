from sqlalchemy.orm import Session
from models.models import Roles

class RoleRepository:
    """Repositorio responsable de las operaciones de base de datos de roles."""
    def __init__(self, db: Session):
        self.db = db

    def list_roles_with_permissions(self):
        """
        Obtiene todos los roles y sus permisos asociados.
        Returns:
            List[Roles]: Lista de roles con sus permisos cargados
        """
        return self.db.query(Roles).all() 