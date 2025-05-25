from typing import List
from sqlalchemy.orm import Session
from models.models import UserDevices
import logging

logger = logging.getLogger(__name__)

class UserDeviceRepository:
    """Repositorio responsable de las operaciones de base de datos de UserDevices."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_user_id(self, user_id: int) -> List[UserDevices]:
        """
        Obtiene todos los dispositivos de un usuario.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Lista de dispositivos del usuario
        """
        return self.db.query(UserDevices).filter(UserDevices.user_id == user_id).all() 