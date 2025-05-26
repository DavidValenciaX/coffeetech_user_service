from dataclasses import dataclass
from typing import Optional
import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

load_dotenv(override=True, encoding='utf-8')


@dataclass
class EmailConfiguration:
    """Configuration class for email settings."""
    
    smtp_user: str
    smtp_pass: str
    smtp_host: str
    smtp_port: int
    app_base_url: str
    logo_url: str
    fallback_logo_url: str
    
    @classmethod
    def from_environment(cls) -> 'EmailConfiguration':
        """Create configuration from environment variables."""
        smtp_user = os.getenv("SMTP_USER")
        smtp_pass = os.getenv("SMTP_PASS")
        
        if not smtp_user or not smtp_pass:
            logger.error("Las credenciales SMTP no están configuradas correctamente.")
            raise ValueError("SMTP credentials are not properly configured")
        
        # Get base URL configuration
        app_host = os.getenv("APP_BASE_URL", "http://localhost")
        app_port = os.getenv("PORT", "8000")
        app_base_url = f"{app_host}:{app_port}"
        
        return cls(
            smtp_user=smtp_user,
            smtp_pass=smtp_pass,
            smtp_host="smtp.zoho.com",
            smtp_port=465,
            app_base_url=app_base_url,
            logo_url=f"{app_base_url}/static/logo.jpeg",
            fallback_logo_url="https://res.cloudinary.com/dh58mbonw/image/upload/v1745059649/u4iwdb6nsupnnsqwkvcn.jpg"
        )
    
    def validate(self) -> bool:
        """Validate that all required configuration is present."""
        return all([
            self.smtp_user,
            self.smtp_pass,
            self.smtp_host,
            self.smtp_port,
            self.app_base_url
        ]) 