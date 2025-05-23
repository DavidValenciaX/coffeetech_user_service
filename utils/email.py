import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

load_dotenv(override=True, encoding='utf-8')

def send_email(email, token, email_type, farm_name=None, owner_name=None, suggested_role=None):
    """
    Envía un correo electrónico basado en el tipo especificado.

    :param email: Dirección de correo electrónico del destinatario.
    :param token: Token a incluir en el cuerpo del correo electrónico.
    :param email_type: Tipo de correo a enviar ('verification', 'reset' o 'invitation').
    :param farm_name: Nombre de la finca (opcional, solo para invitación).
    :param owner_name: Nombre del dueño (opcional, solo para invitación).
    :param suggested_role: Rol sugerido para el invitado (opcional, solo para invitación).
    """
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")

    if not smtp_user or not smtp_pass:
        logger.error("Las credenciales SMTP no están configuradas correctamente.")
        return

    smtp_host = "smtp.zoho.com"
    smtp_port = 465
    
    # Obtener la URL base y el puerto de la aplicación desde variables de entorno
    app_host = os.getenv("APP_BASE_URL", "http://localhost")
    app_port = os.getenv("PORT", "8000") # Default to 8000 if not set
    app_base_url = f"{app_host}:{app_port}"
    
    # Usar directamente las URLs para el logo en lugar de variables de entorno
    # Primero intentamos con la URL del servidor, y si hay problemas, usamos la URL de Cloudinary como respaldo
    logo_url = f"{app_base_url}/static/logo.jpeg" 
    fallback_logo_url = "https://res.cloudinary.com/dh58mbonw/image/upload/v1745059649/u4iwdb6nsupnnsqwkvcn.jpg"

    # Definir el asunto y el cuerpo del correo basado en el tipo de correo
    if email_type == 'verification':
        subject = "Verificación de Correo Electrónico"
        body_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background-color: #f7f7f7;
                    margin: 0;
                    padding: 0;
                }}
                .container {{
                    width: 100%;
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: #ffffff;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                }}
                .header {{
                    text-align: center;
                    padding-bottom: 20px;
                }}
                .logo {{
                    max-width: 150px;
                    height: auto;
                    margin-bottom: 20px;
                }}
                .content {{
                    text-align: center;
                }}
                .token-box {{
                    background-color: #f2f2f2;
                    padding: 10px;
                    border-radius: 5px;
                    display: inline-block;
                    margin: 20px 0;
                    font-size: 18px;
                    font-weight: bold;
                }}
                .footer {{
                    margin-top: 30px;
                    text-align: center;
                    font-size: 12px;
                    color: #777;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <img src="{logo_url}" alt="Logo de CoffeTech" class="logo" onerror="this.onerror=null;this.src='{fallback_logo_url}';">
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
    elif email_type == 'reset':
        subject = "Restablecimiento de Contraseña"
        body_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background-color: #f7f7f7;
                    margin: 0;
                    padding: 0;
                }}
                .container {{
                    width: 100%;
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: #ffffff;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                }}
                .header {{
                    text-align: center;
                    padding-bottom: 20px;
                }}
                .logo {{
                    max-width: 150px;
                    height: auto;
                    margin-bottom: 20px;
                }}
                .content {{
                    text-align: center;
                }}
                .token-box {{
                    background-color: #f2f2f2;
                    padding: 10px;
                    border-radius: 5px;
                    display: inline-block;
                    margin: 20px 0;
                    font-size: 18px;
                    font-weight: bold;
                }}
                .footer {{
                    margin-top: 30px;
                    text-align: center;
                    font-size: 12px;
                    color: #777;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <img src="{logo_url}" alt="Logo de CoffeTech" class="logo" onerror="this.onerror=null;this.src='{fallback_logo_url}';">
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
    elif email_type == 'invitation':
        subject = "Invitación a CoffeTech"
        body_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background-color: #f7f7f7;
                    margin: 0;
                    padding: 0;
                }}
                .container {{
                    width: 100%;
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: #ffffff;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                }}
                .header {{
                    text-align: center;
                    padding-bottom: 20px;
                }}
                .logo {{
                    max-width: 150px;
                    height: auto;
                    margin-bottom: 20px;
                }}
                .content {{
                    text-align: center;
                }}
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
                    background-color: #4CAF50; /* Verde */
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                }}
                .button.reject {{
                    background-color: #f44336; /* Rojo */
                }}
                .footer {{
                    margin-top: 30px;
                    text-align: center;
                    font-size: 12px;
                    color: #777;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <img src="{logo_url}" alt="Logo de CoffeTech" class="logo" onerror="this.onerror=null;this.src='{fallback_logo_url}';">
                    <h2>Hola,</h2>
                </div>
                <div class="content">
                    <p>Has sido invitado a unirte como <strong>{suggested_role}</strong> a la finca <strong>{farm_name}</strong> por <strong>{owner_name}</strong>.</p>
                    
                    <p>¡Te esperamos!</p>
                    <a href="{app_base_url}/invitation/accept-invitation/{token}" class="button">Aceptar Invitación</a>
                    <a href="{app_base_url}/invitation/reject-invitation/{token}" class="button reject">Rechazar Invitación</a>
                </div>
                <div class="footer">
                    <p>Gracias,<br/>El equipo de CoffeTech</p>
                </div>
            </div>
        </body>
        </html>
        """
    else:
        logger.error(f"Tipo de correo no reconocido: {email_type}")
        return

    # Crear el mensaje de correo electrónico
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = email

    # Agregar cuerpo en formato HTML
    msg.attach(MIMEText(body_html, "html"))

    try:
        # Conectar al servidor SMTP de Zoho usando SSL
        with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, email, msg.as_string())
        logger.info(f"Correo de {email_type} enviado a {email}.")
    except Exception as e:
        logger.error(f"Error al enviar correo a {email}: {e}")
