from typing import Optional
from sqlalchemy.orm import Session
from models.models import UserStates
import logging

logger = logging.getLogger(__name__)


class UserStateConstants:
    """Constantes para los estados de usuario para evitar magic strings."""
    ACTIVE = "Activo"
    VERIFIED = "Verificado"
    UNVERIFIED = "No Verificado"
    SUSPENDED = "Suspendido"


class UserStateNotFoundError(Exception):
    """Exception raised when a required user state is not found in the database."""
    pass


class UserStateRepository:
    """Repositorio responsable de las operaciones de base de datos de estados de usuario."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_state_by_name(self, state_name: str) -> Optional[UserStates]:
        """
        Obtiene el estado para la entidad Users por nombre.
        
        Args:
            state_name (str): Nombre del estado a obtener (e.g., "Activo", "Inactivo", "No Verificado", "Verificado").
            
        Returns:
            El objeto UserStates si se encuentra, None en caso contrario.
        """
        try:
            return self.db.query(UserStates).filter(UserStates.name == state_name).first()
        except Exception as e:
            logger.error(f"Error al obtener el estado de usuario '{state_name}': {str(e)}")
            return None 