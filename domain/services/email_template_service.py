from typing import Dict, Any
from .email_configuration import EmailConfiguration


class EmailTemplateService:
    """Service responsible for generating email templates."""
    
    def __init__(self, config: EmailConfiguration):
        self.config = config
    
    def generate_verification_email(self, token: str) -> Dict[str, str]:
        """
        Generate verification email template.
        
        Args:
            token: Verification token
            
        Returns:
            Dict containing subject and HTML body
        """
        subject = "Verificación de Correo Electrónico"
        body_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                {self._get_email_styles()}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <img src="{self.config.logo_url}" alt="Logo de CoffeTech" class="logo" onerror="this.onerror=null;this.src='{self.config.fallback_logo_url}';">
                    <h2>Hola,</h2>
                </div>
                <div class="content">
                    <p>Gracias por registrarte en Coffeetech. Por favor, verifica tu dirección de correo electrónico usando el siguiente código:</p>
                    <div class="token-box" id="token">{token}</div>
                    <p>Por favor, copia el código anterior para verificar tu cuenta.</p>
                </div>
                <div class="footer">
                    <p>Gracias,<br/>El equipo de CoffeTech</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return {"subject": subject, "body_html": body_html}
    
    def generate_password_reset_email(self, token: str) -> Dict[str, str]:
        """
        Generate password reset email template.
        
        Args:
            token: Password reset token
            
        Returns:
            Dict containing subject and HTML body
        """
        subject = "Restablecimiento de Contraseña"
        body_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                {self._get_email_styles()}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <img src="{self.config.logo_url}" alt="Logo de CoffeTech" class="logo" onerror="this.onerror=null;this.src='{self.config.fallback_logo_url}';">
                    <h2>Hola,</h2>
                </div>
                <div class="content">
                    <p>Hemos recibido una solicitud para restablecer tu contraseña. Utiliza el siguiente código para continuar:</p>
                    <div class="token-box" id="token">{token}</div>
                    <p>Por favor, copia el código anterior para restablecer tu contraseña.</p>
                    <p>Ten en cuenta que vence en 15 minutos.</p>
                </div>
                <div class="footer">
                    <p>Si no solicitaste restablecer tu contraseña, ignora este correo.</p>
                    <p>Gracias,<br/>El equipo de CoffeTech</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return {"subject": subject, "body_html": body_html}
    
    def generate_invitation_email(self, token: str, farm_name: str, owner_name: str, role: str) -> Dict[str, str]:
        """
        Generate invitation email template.
        
        Args:
            token: Invitation token
            farm_name: Name of the farm
            owner_name: Name of the farm owner
            role: Suggested role for the invitee
            
        Returns:
            Dict containing subject and HTML body
        """
        subject = "Invitación a CoffeTech"
        body_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                {self._get_email_styles()}
                .invitation-box {{
                    background-color: #e0f7fa;
                    padding: 10px;
                    border-radius: 5px;
                    display: inline-block;
                    margin: 20px 0;
                    font-size: 18px;
                    font-weight: bold;
                }}
                .button {{
                    display: inline-block;
                    margin: 10px;
                    padding: 10px 20px;
                    background-color: #4CAF50;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                }}
                .button.reject {{
                    background-color: #f44336;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <img src="{self.config.logo_url}" alt="Logo de CoffeTech" class="logo" onerror="this.onerror=null;this.src='{self.config.fallback_logo_url}';">
                    <h2>Hola,</h2>
                </div>
                <div class="content">
                    <p>Has sido invitado a unirte como <strong>{role}</strong> a la finca <strong>{farm_name}</strong> por <strong>{owner_name}</strong>.</p>
                    
                    <p>¡Te esperamos!</p>
                    <a href="{self.config.app_base_url}/invitation/accept-invitation/{token}" class="button">Aceptar Invitación</a>
                    <a href="{self.config.app_base_url}/invitation/reject-invitation/{token}" class="button reject">Rechazar Invitación</a>
                </div>
                <div class="footer">
                    <p>Gracias,<br/>El equipo de CoffeTech</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return {"subject": subject, "body_html": body_html}
    
    def _get_email_styles(self) -> str:
        """Get common CSS styles for emails."""
        return """
                body {
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background-color: #f7f7f7;
                    margin: 0;
                    padding: 0;
                }
                .container {
                    width: 100%;
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: #ffffff;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                }
                .header {
                    text-align: center;
                    padding-bottom: 20px;
                }
                .logo {
                    max-width: 150px;
                    height: auto;
                    margin-bottom: 20px;
                }
                .content {
                    text-align: center;
                }
                .token-box {
                    background-color: #f2f2f2;
                    padding: 10px;
                    border-radius: 5px;
                    display: inline-block;
                    margin: 20px 0;
                    font-size: 18px;
                    font-weight: bold;
                }
                .footer {
                    margin-top: 30px;
                    text-align: center;
                    font-size: 12px;
                    color: #777;
                }
        """ 