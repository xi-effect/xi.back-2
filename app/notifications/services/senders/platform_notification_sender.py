from tmexio import Emitter

from app.communities.rooms import user_room
from app.notifications.models.notifications_db import Notification
from app.notifications.services.senders.base_notification_sender import (
    BaseNotificationSender,
)


class PlatformNotificationSender(BaseNotificationSender):
    def __init__(
        self,
        notification: Notification,
        emitter: Emitter[Notification],
    ) -> None:
        super().__init__(notification=notification)
        self.emitter = emitter

    async def send_notification(self, recipient_user_id: int) -> None:
        await self.emitter.emit(self.notification, target=user_room(recipient_user_id))
