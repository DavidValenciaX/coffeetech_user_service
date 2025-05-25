from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from domain.repositories import UserDeviceRepository
import logging

logger = logging.getLogger(__name__)

class UserDeviceService:
    """Servicio de dominio para la gestión de dispositivos de usuario."""
    
    def __init__(self, db: Session):
        self.db = db
        self.user_device_repository = UserDeviceRepository(db)
    
    def get_user_devices(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Obtiene todos los dispositivos de un usuario.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Lista de dispositivos del usuario
            
        Raises:
            SQLAlchemyError: Si hay error en la base de datos
        """
        try:
            devices = self.user_device_repository.get_by_user_id(user_id)
            return [
                {
                    "user_device_id": device.user_device_id,
                    "user_id": device.user_id,
                    "fcm_token": device.fcm_token
                }
                for device in devices
            ]
        except SQLAlchemyError as e:
            logger.error(f"Error getting user devices for user {user_id}: {str(e)}")
            raise 