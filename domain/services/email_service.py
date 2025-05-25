import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import logging
from typing import Optional

logger = logging.getLogger(__name__)

load_dotenv(override=True, encoding='utf-8')


class EmailService:
    """Service responsible for sending different types of emails."""
    
    def __init__(self):
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_pass = os.getenv("SMTP_PASS")
        self.smtp_host = "smtp.zoho.com"
        self.smtp_port = 465
        
        # Get base URL configuration
        app_host = os.getenv("APP_BASE_URL", "http://localhost")
        app_port = os.getenv("PORT", "8000")
        self.app_base_url = f"{app_host}:{app_port}"
        
        # Logo URLs
        self.logo_url = f"{self.app_base_url}/static/logo.jpeg"
        self.fallback_logo_url = "https://res.cloudinary.com/dh58mbonw/image/upload/v1745059649/u4iwdb6nsupnnsqwkvcn.jpg"
        
        if not self.smtp_user or not self.smtp_pass:
            logger.error("Las credenciales SMTP no están configuradas correctamente.")
    
    def send_verification_email(self, email: str, token: str) -> bool:
        """
        Send a verification email to the user.
        
        Args:
            email: User's email address
            token: Verification token
            
        Returns:
            bool: True if email was sent successfully, False otherwise
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
                    <img src="{self.logo_url}" alt="Logo de CoffeTech" class="logo" onerror="this.onerror=null;this.src='{self.fallback_logo_url}';">
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
        
        return self._send_email(email, subject, body_html)
    
    def send_password_reset_email(self, email: str, token: str) -> bool:
        """
        Send a password reset email to the user.
        
        Args:
            email: User's email address
            token: Password reset token
            
        Returns:
            bool: True if email was sent successfully, False otherwise
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
                    <img src="{self.logo_url}" alt="Logo de CoffeTech" class="logo" onerror="this.onerror=null;this.src='{self.fallback_logo_url}';">
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
        
        return self._send_email(email, subject, body_html)
    
    def send_invitation_email(self, email: str, token: str, farm_name: str, owner_name: str, role: str) -> bool:
        """
        Send an invitation email to join a farm.
        
        Args:
            email: User's email address
            token: Invitation token
            farm_name: Name of the farm
            owner_name: Name of the farm owner
            role: Suggested role for the invitee
            
        Returns:
            bool: True if email was sent successfully, False otherwise
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
                    <img src="{self.logo_url}" alt="Logo de CoffeTech" class="logo" onerror="this.onerror=null;this.src='{self.fallback_logo_url}';">
                    <h2>Hola,</h2>
                </div>
                <div class="content">
                    <p>Has sido invitado a unirte como <strong>{role}</strong> a la finca <strong>{farm_name}</strong> por <strong>{owner_name}</strong>.</p>
                    
                    <p>¡Te esperamos!</p>
                    <a href="{self.app_base_url}/invitation/accept-invitation/{token}" class="button">Aceptar Invitación</a>
                    <a href="{self.app_base_url}/invitation/reject-invitation/{token}" class="button reject">Rechazar Invitación</a>
                </div>
                <div class="footer">
                    <p>Gracias,<br/>El equipo de CoffeTech</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(email, subject, body_html)
    
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
    
    def _send_email(self, email: str, subject: str, body_html: str) -> bool:
        """
        Send an email with the given subject and HTML body.
        
        Args:
            email: Recipient's email address
            subject: Email subject
            body_html: HTML body content
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        if not self.smtp_user or not self.smtp_pass:
            logger.error("Las credenciales SMTP no están configuradas correctamente.")
            return False
        
        # Create email message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.smtp_user
        msg["To"] = email
        
        # Add HTML body
        msg.attach(MIMEText(body_html, "html"))
        
        try:
            # Connect to Zoho SMTP server using SSL
            with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port) as server:
                server.login(self.smtp_user, self.smtp_pass)
                server.sendmail(self.smtp_user, email, msg.as_string())
            logger.info(f"Email enviado exitosamente a {email}")
            return True
        except Exception as e:
            logger.error(f"Error al enviar correo a {email}: {e}")
            return False


# Global instance of the email service
email_service = EmailService() 