from app.common.fastapi_ext import APIRouterExt
from app.common.schemas.notifications_sch import NotificationInputSchema
from app.communities.rooms import user_room
from app.notifications.models.notifications_db import Notification
from app.notifications.models.recipient_notifications_db import RecipientNotification
from app.notifications.routes.notifications_sio import NewNotificationEmitter

router = APIRouterExt(tags=["notifications mub"])


@router.post(
    path="/notifications/",
    response_model=Notification.ResponseSchema,
    summary="Send a new notification to multiple users by ids",
)
async def send_notification(
    emitter: NewNotificationEmitter,
    data: NotificationInputSchema,
) -> Notification:
    notification = await Notification.create(payload=data.payload)
    for recipient_user_id in data.recipient_user_ids:
        await RecipientNotification.create(
            notification_id=notification.id,
            recipient_user_id=recipient_user_id,
        )

    for recipient_user_id in data.recipient_user_ids:
        await emitter.emit(
            notification,
            target=user_room(recipient_user_id),
        )

    return notification
