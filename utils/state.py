from sqlalchemy.orm import Session
from models.models import UserStates
import logging

logger = logging.getLogger(__name__)

def get_user_state(db: Session, state_name: str):
    """
    Obtiene el estado para la entidad Users.
    
    Args:
        db (Session): Sesión de la base de datos.
        state_name (str): Nombre del estado a obtener (e.g., "Activo", "Inactivo", "No Verificado", "Verificado").
        
    Returns:
        El objeto UserStates si se encuentra, None en caso contrario.
    """
    try:
        return db.query(UserStates).filter(UserStates.name == state_name).first()
    except Exception as e:
        logger.error(f"Error al obtener el estado de usuario '{state_name}': {str(e)}")
        return None