from typing import Annotated

from tmexio import Emitter

from app.common.config import tmex
from app.notifications.models.notifications_db import Notification

NewNotificationEmitter = Annotated[
    Emitter[Notification],
    tmex.register_server_emitter_fastapi_depends(
        body_annotation=Notification.ResponseSchema,
        event_name="new-notification",
        summary="A new notification has been sent to the current user",
        tags=["notifications"],
    ),
]
