import asyncio

from faststream.redis import RedisRouter

from app.common.config import settings
from app.common.faststream_ext import build_stream_sub
from app.common.schemas.notifications_sch import NotificationInputSchema
from app.notifications.models.notifications_db import Notification
from app.notifications.models.recipient_notifications_db import RecipientNotification
from app.notifications.routes.notifications_sio import NewNotificationEmitter
from app.notifications.services.senders import (
    email_notification_sender,
    platform_notification_sender,
    telegram_notification_sender,
)

router = RedisRouter()


@router.subscriber(  # type: ignore[misc]  # bad typing in faststream
    stream=build_stream_sub(
        stream_name=settings.notifications_send_stream_name,
        service_name="notification-service",
    ),
    # TODO handle exceptions (retry?)
)
async def send_notification(
    emitter: NewNotificationEmitter,
    data: NotificationInputSchema,
) -> None:
    recipient_user_ids = list(set(data.recipient_user_ids))

    notification = await Notification.create(payload=data.payload)

    await RecipientNotification.create_batch(
        {
            "notification_id": notification.id,
            "recipient_user_id": recipient_user_id,
        }
        for recipient_user_id in recipient_user_ids
    )

    await asyncio.gather(
        *platform_notification_sender.PlatformNotificationSender(
            notification=notification,
            emitter=emitter,
        ).generate_tasks(recipient_user_ids=recipient_user_ids),
        *email_notification_sender.EmailNotificationSender(
            notification=notification
        ).generate_tasks(recipient_user_ids=recipient_user_ids),
        *telegram_notification_sender.TelegramNotificationSender(
            notification=notification,
        ).generate_tasks(recipient_user_ids=recipient_user_ids),
        # TODO handle partial failure with `return_exceptions=True`
    )
