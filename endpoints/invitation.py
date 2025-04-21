from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session, joinedload
from models.models import UserRoleFarm, User, Role, Permission, RolePermission, Invitation
from utils.security import verify_session_token
from dataBase import get_db_session
import logging
from utils.FCM import send_fcm_notification
from models.models import UserRoleFarm, User, Role, Permission, RolePermission, Invitation, Notification
from fastapi import APIRouter, Depends
from utils.response import create_response
from utils.response import session_token_invalid_response
from utils.status import get_status
from models.models import NotificationType
import pytz

bogota_tz = pytz.timezone("America/Bogota")

from datetime import datetime
from models.models import Invitation, Notification

# Configuración básica de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

class InvitationCreate(BaseModel):
    """
    Modelo para la creación de una invitación.

    Attributes:
        email (EmailStr): Dirección de correo electrónico del usuario a invitar.
        suggested_role_id (int): ID del rol sugerido para el usuario invitado.
        farm_id (int): Identificador de la finca a la que se invita.
    """
    email: EmailStr
    suggested_role_id: int
    farm_id: int

@router.post("/create-invitation")
def create_invitation(invitation_data: InvitationCreate, session_token: str, db: Session = Depends(get_db_session)):
    """
    Creates an invitation for a registered user to join a specific farm with a suggested role.

    Requires a valid `session_token` for the inviting user provided as a query parameter or header.
    The inviting user must have the necessary permissions (`add_administrator_farm` or `add_operator_farm`)
    associated with their role on the specified farm.

    - **email**: Email address of the user to invite. Must be a registered user.
    - **suggested_role_id**: ID of the role suggested for the invited user.
    - **farm_id**: ID of the farm the user is being invited to.

    Checks for existing active associations or pending invitations for the user to the farm.
    Creates an `Invitation` record and a corresponding `Notification` for the invited user.
    Sends an FCM notification if the invited user has an FCM token.
    Returns an error if the inviting user lacks permissions, the invited user is already active
    on the farm, has a pending invitation, or if the invited user is not registered.
    """
    # Validar el session_token y obtener el usuario autenticado (el invitador)
    user = verify_session_token(session_token, db)
    if not user:
        return session_token_invalid_response()
    
    # Verificar si la finca existe
    # TO DO: La nueva verificación de la finca se debe hacer por http al microservicio de fincas

    # Verificar si el usuario (invitador) está asociado a la finca y cuál es su rol
    active_status = get_status(db, "Activo", "User_Role_Farm")
    if not active_status:
        return create_response("error", "El estado 'Activo' no fue encontrado para 'User_Role_Farm'", status_code=400)

    user_role_farm = db.query(UserRoleFarm).filter(
        UserRoleFarm.user_id == user.user_id,
        UserRoleFarm.farm_id == invitation_data.farm_id,
        UserRoleFarm.status_id == active_status.status_id  # Usar el estado "Activo"
    ).first()

    if not user_role_farm:
        return create_response("error", "No tienes acceso a esta finca", status_code=403)

    # Verificar si el rol sugerido para la invitación es válido
    suggested_role = db.query(Role).filter(Role.role_id == invitation_data.suggested_role_id).first()
    if not suggested_role:
        return create_response("error", "El rol sugerido no es válido", status_code=400)

    # Verificar si el rol del usuario (invitador) tiene el permiso adecuado para invitar al rol sugerido
    if suggested_role.name == "Administrador de finca":
        has_permission_to_invite = db.query(RolePermission).join(Permission).filter(
            RolePermission.role_id == user_role_farm.role_id,
            Permission.name == "add_administrator_farm"
        ).first()
        if not has_permission_to_invite:
            return create_response("error", "No tienes permiso para invitar a un Administrador de Finca", status_code=403)

    elif suggested_role.name == "Operador de campo":
        has_permission_to_invite = db.query(RolePermission).join(Permission).filter(
            RolePermission.role_id == user_role_farm.role_id,
            Permission.name == "add_operator_farm"
        ).first()
        if not has_permission_to_invite:
            return create_response("error", "No tienes permiso para invitar a un Operador de Campo", status_code=403)

    else:
        return create_response("error", f"No puedes invitar a colaboradores de rol {suggested_role.name} ", status_code=403)

    # Verificar si el usuario ya está registrado
    existing_user = db.query(User).filter(User.email == invitation_data.email).first()
    if not existing_user:
        return create_response("error", "El usuario no está registrado", status_code=404)

    # Verificar si el usuario ya pertenece a la finca
    active_status = get_status(db, "Activo", "User_Role_Farm")
    if not active_status:
        return create_response("error", "El estado 'Activo' no fue encontrado para 'User_Role_Farm'", status_code=400)

    existing_role_farm = db.query(UserRoleFarm).filter(
        UserRoleFarm.user_id == existing_user.user_id,
        UserRoleFarm.farm_id == invitation_data.farm_id,
        UserRoleFarm.status_id == active_status.status_id  # Verificar que esté en estado 'Activo'
    ).first()

    if existing_role_farm:
        return create_response("error", "El usuario ya está asociado a la finca con un estado activo", status_code=400)

    # Verificar si el usuario ya tiene una invitación pendiente
    pending_status = get_status(db, "Pendiente", "Invitation")
    if not pending_status:
        return create_response("error", "El estado 'Pendiente' no fue encontrado para 'Invitation'", status_code=400)

    existing_invitation = db.query(Invitation).filter(
        Invitation.email == invitation_data.email,
        Invitation.farm_id == invitation_data.farm_id,
        Invitation.status_id == pending_status.status_id  # Usar el estado "Pendiente"
    ).first()

    if existing_invitation:
        return create_response("error", "El usuario ya tiene una invitación pendiente para esta finca", status_code=400)

    # Crear la invitación y la notificación solo después de todas las verificaciones
    try:
        # Crear la nueva invitación
        new_invitation = Invitation(
            email=invitation_data.email,
            suggested_role_id=invitation_data.suggested_role_id,
            farm_id=invitation_data.farm_id,
            inviter_user_id=user.user_id,  # Agregar el ID del usuario que está creando la invitación
            date=datetime.now(bogota_tz)  # Agregar la fecha actual
        )
        db.add(new_invitation)
        db.commit()
        db.refresh(new_invitation)

        # Crear la notificación asociada con notification_type_id
        pending_status = get_status(db, "Pendiente", "Notification")
        if not pending_status:
            db.rollback() # Rollback if status not found
            return create_response("error", "El estado 'Pendiente' no fue encontrado para 'Notification'", status_code=400)

        invitation_notification_type = db.query(NotificationType).filter(NotificationType.name == "Invitation").first()
        if not invitation_notification_type:
            db.rollback() # Rollback if type not found
            return create_response("error", "No se encontró el tipo de notificación 'Invitation'", status_code=400)

        new_notification = Notification(
            message=f"Has sido invitado como {suggested_role.name} a la finca TODO: farm.name",
            date=datetime.now(bogota_tz),
            user_id=existing_user.user_id,
            notification_type_id=invitation_notification_type.notification_type_id,  # Usar notification_type_id
            invitation_id=new_invitation.invitation_id,
            farm_id=invitation_data.farm_id,
            status_id=pending_status.status_id  # Estado "Pendiente" del tipo "Notification"
        )
        db.add(new_notification)
        db.commit()
        db.refresh(new_invitation)
        db.refresh(new_notification)

    
        # Enviar notificación FCM al usuario
        if fcm_token := existing_user.fcm_token:
            title = "Nueva Invitación"
            body = f"Has sido invitado como {suggested_role.name} a la finca TODO: farm.name"
            send_fcm_notification(fcm_token, title, body)
        else:
            logger.warning("No se pudo enviar la notificación push. No se encontró el token FCM del usuario.")
    except Exception as e:
        db.rollback()  # Hacer rollback en caso de un error
        logger.error(f"Error creando la invitación: {str(e)}")
        return create_response("error", f"Error creando la invitación: {str(e)}", status_code=500)

    return create_response("success", "Invitación creada exitosamente", {"invitation_id": new_invitation.invitation_id}, status_code=201)


@router.post("/respond-invitation/{invitation_id}")
def respond_invitation(invitation_id: int, action: str, session_token: str, db: Session = Depends(get_db_session)):
    """
    Allows an invited user to accept or reject an invitation.

    Requires a valid `session_token` for the invited user provided as a query parameter or header.

    - **invitation_id**: The ID of the invitation being responded to (path parameter).
    - **action**: The response action, must be either 'accept' or 'reject' (query parameter).

    Verifies that the authenticated user is the recipient of the invitation.
    Updates the status of the `Invitation` and the related `Notification`.
    If accepted:
        - Creates a `UserRoleFarm` record associating the user with the farm and the suggested role.
        - Creates a notification for the user who sent the invitation.
        - Sends an FCM notification to the inviter.
    If rejected:
        - Creates a notification for the user who sent the invitation.
        - Sends an FCM notification to the inviter.
    Returns an error if the invitation is not found, the user is not the recipient,
    the invitation has already been processed, or the action is invalid.
    """
    # Validar el session_token y obtener el usuario autenticado
    user = verify_session_token(session_token, db)
    if not user:
        return session_token_invalid_response()

    # Buscar la invitación
    invitation = db.query(Invitation).options(joinedload(Invitation.suggested_role)).filter(Invitation.invitation_id == invitation_id).first()
    if not invitation:
        return create_response("error", "Invitación no encontrada", status_code=404)
    
    # Verificar si el usuario es el invitado
    if user.email != invitation.email:
        return create_response("error", "No tienes permiso para responder esta invitación", status_code=403)

    # Usar get_status para obtener los estados "Aceptada" y "Rechazada" del tipo "Invitation"
    accepted_status = get_status(db, "Aceptada", "Invitation")
    rejected_status = get_status(db, "Rechazada", "Invitation")
    responded_status = get_status(db, "Respondida", "Notification")  # Obtener el estado "Respondida"

    if not accepted_status or not rejected_status or not responded_status:
        return create_response("error", "Estados necesarios no encontrados en la base de datos", status_code=500)

    # Verificar si la invitación ya fue aceptada o rechazada
    if invitation.status_id in [accepted_status.status_id, rejected_status.status_id]:
        return create_response("error", "La invitación ya ha sido procesada (aceptada o rechazada)", status_code=400)

    # Actualizar las notificaciones relacionadas con la invitación
    notification = db.query(Notification).filter(Notification.invitation_id == invitation_id).first()
    if notification:
        notification.status_id = responded_status.status_id  # Actualizar el estado a "Respondida"
        db.commit()

    # Verificar si la acción es "accept" o "reject"
    if action.lower() == "accept":
        # Cambiar el estado de la invitación a "Aceptada"
        invitation.status_id = accepted_status.status_id
        db.commit()

        # Usar la función get_status para obtener el estado "Activo" del tipo "User_Role_Farm"
        active_status = get_status(db, "Activo", "User_Role_Farm")
        if not active_status:
            db.rollback()
            return create_response("error", "El estado 'Activo' no fue encontrado para 'User_Role_Farm'", status_code=400)

        # Agregar al usuario a la finca en la tabla UserRoleFarm con el rol de la invitación
        new_user_role_farm = UserRoleFarm(
            user_id=user.user_id,
            farm_id=invitation.farm_id,
            role_id=invitation.suggested_role_id,  # Asignar el rol sugerido
            status_id=active_status.status_id  # Estado "Activo" del tipo "User_Role_Farm"
        )
        db.add(new_user_role_farm)

        # Crear la notificación para el usuario que hizo la invitación (inviter_user_id)
        inviter = db.query(User).filter(User.user_id == invitation.inviter_user_id).first()
        if inviter:
            accepted_notification_type = db.query(NotificationType).filter(NotificationType.name == "Invitation_accepted").first()
            if not accepted_notification_type:
                db.rollback()
                return create_response("error", "No se encontró el tipo de notificación 'Invitation_accepted'", status_code=400)

            notification_message = f"El usuario {user.name} ha aceptado tu invitación como {invitation.suggested_role.name} a la finca TODO: farm.name."
            new_notification = Notification(
                message=notification_message,
                date=datetime.now(bogota_tz),
                user_id=invitation.inviter_user_id,
                notification_type_id=accepted_notification_type.notification_type_id,  # Usar notification_type_id
                invitation_id=invitation.invitation_id,
                farm_id=invitation.farm_id,
                status_id=responded_status.status_id  # Estado "Respondida" del tipo "Notification"
            )
            db.add(new_notification)

            # Commit all changes together: invitation status, user_role_farm, notification
            db.commit()

            # Enviar notificación FCM al invitador (si tiene token)
            if inviter.fcm_token:
                send_fcm_notification(inviter.fcm_token, "Invitación aceptada", notification_message)
        else:
             db.commit() # Commit invitation status and user_role_farm even if inviter not found

        return create_response("success", "Has aceptado la invitación exitosamente", status_code=200)

    elif action.lower() == "reject":
        # Cambiar el estado de la invitación a "Rechazada"
        invitation.status_id = rejected_status.status_id

        # Crear la notificación para el usuario que hizo la invitación (inviter_user_id)
        inviter = db.query(User).filter(User.user_id == invitation.inviter_user_id).first()
        if inviter:
            rejected_notification_type = db.query(NotificationType).filter(NotificationType.name == "invitation_rejected").first()
            if not rejected_notification_type:
                db.rollback()
                return create_response("error", "No se encontró el tipo de notificación 'invitation_rejected'", status_code=400)

            notification_message = f"El usuario {user.name} ha rechazado tu invitación como {invitation.suggested_role.name} a la finca TODO: farm.name."
            new_notification = Notification(
                message=notification_message,
                date=datetime.now(bogota_tz),
                user_id=invitation.inviter_user_id,
                notification_type_id=rejected_notification_type.notification_type_id,  # Usar notification_type_id
                invitation_id=invitation.invitation_id,
                farm_id=invitation.farm_id,
                status_id=responded_status.status_id  # Estado "Respondida" del tipo "Notification"
            )
            db.add(new_notification)

            # Commit invitation status and notification together
            db.commit()

            # Enviar notificación FCM al invitador (si tiene token)
            if inviter.fcm_token:
                send_fcm_notification(inviter.fcm_token, "Invitación rechazada", notification_message)
        else:
            db.commit() # Commit invitation status even if inviter not found

        return create_response("success", "Has rechazado la invitación exitosamente", status_code=200)

    else:
        return create_response("error", "Acción inválida. Debes usar 'accept' o 'reject'", status_code=400)