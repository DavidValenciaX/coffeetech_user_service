import sys
import os
from dataclasses import dataclass
from typing import Optional
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
        
        is_testing = "pytest" in sys.modules

        if not smtp_user or not smtp_pass:
            if is_testing:
                logger.warning(
                    "SMTP_USER or SMTP_PASS environment variables not set. "
                    "Using dummy values for testing environment as 'pytest' is in sys.modules."
                )
                smtp_user = smtp_user or "dummy_smtp_user@example.com"
                smtp_pass = smtp_pass or "dummy_smtp_password"
            else:
                logger.error(
                    "Las credenciales SMTP (SMTP_USER, SMTP_PASS) no están configuradas "
                    "correctamente en las variables de entorno."
                )
                raise ValueError("SMTP credentials are not properly configured in environment variables")
        
        app_host = os.getenv("APP_BASE_URL", "http://localhost")
        app_port = os.getenv("PORT", "8000")
        app_base_url = f"{app_host}:{app_port}"
        
        smtp_host_env = os.getenv("SMTP_HOST", "smtp.zoho.com")
        smtp_port_env = os.getenv("SMTP_PORT", "465")
        
        try:
            smtp_port_int = int(smtp_port_env)
        except ValueError:
            logger.error(f"Invalid SMTP_PORT: '{smtp_port_env}'. Must be an integer.")
            if is_testing:
                logger.warning(f"Using default SMTP_PORT 465 for testing due to invalid value: {smtp_port_env}")
                smtp_port_int = 465 # Default port for testing if invalid
            else:
                raise ValueError(f"Invalid SMTP_PORT: '{smtp_port_env}'. Must be an integer.")

        return cls(
            smtp_user=smtp_user,
            smtp_pass=smtp_pass,
            smtp_host=smtp_host_env,
            smtp_port=smtp_port_int,
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
            isinstance(self.smtp_port, int) and self.smtp_port > 0, # Ensure port is a positive integer
            self.app_base_url
        ]) 