import asyncio

import sentry_sdk
from faststream.redis import RedisRouter

from app.common.config import settings
from app.common.faststream_ext import build_stream_sub
from app.common.schemas.notifications_sch import NotificationInputV2Schema
from app.common.sqlalchemy_ext import db
from app.notifications.models.notifications_db import Notification
from app.notifications.models.recipient_notifications_db import RecipientNotification
from app.notifications.routes.notifications_sio import NewNotificationEmitter
from app.notifications.services import recipients_svc
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
    # TODO (197) handle exceptions
)
async def send_notification(
    emitter: NewNotificationEmitter,
    data: NotificationInputV2Schema,
) -> None:
    if await Notification.is_idempotency_violated(idempotency_key=data.idempotency_key):
        # TODO (197) catch the integrity error instead
        return

    recipient_user_ids = (
        await recipients_svc.generate_recipient_user_ids_for_notification(
            notification_data=data,
        )
    )

    if len(recipient_user_ids) == 0:
        return

    notification = await Notification.create(
        payload=data.payload,
        idempotency_key=data.idempotency_key,
        idempotency_expires_at=data.idempotency_expires_at,
    )

    await RecipientNotification.create_batch(
        {
            "notification_id": notification.id,
            "recipient_user_id": recipient_user_id,
        }
        for recipient_user_id in recipient_user_ids
    )

    await db.session.commit()
    # TODO (197) the commit is here to ensure idempotency, but that's not reliable
    #   in future split this into multiple events (first save to db, then send)

    results = await asyncio.gather(
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
        return_exceptions=True,
    )

    for result in results:
        if result is None:
            continue
        sentry_sdk.capture_exception(result)
