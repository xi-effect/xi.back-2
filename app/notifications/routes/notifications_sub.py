from faststream.redis import RedisRouter

from app.common.config import settings
from app.common.faststream_ext import build_stream_sub
from app.common.schemas.notifications_sch import NotificationInputSchema
from app.communities.rooms import user_room
from app.notifications.models.notifications_db import Notification
from app.notifications.models.recipient_notifications_db import RecipientNotification
from app.notifications.routes.notifications_sio import NewNotificationEmitter

router = RedisRouter()


@router.subscriber(  # type: ignore[misc]  # bad typing in faststream
    stream=build_stream_sub(
        stream_name=settings.notifications_send_stream_name,
        service_name="notification-service",
    ),
)
async def send_notification(
    emitter: NewNotificationEmitter,
    data: NotificationInputSchema,
) -> None:
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
