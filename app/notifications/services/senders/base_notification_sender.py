from abc import ABC, abstractmethod
from collections.abc import Awaitable, Iterator

from app.notifications.models.notifications_db import Notification


class BaseNotificationSender(ABC):
    def __init__(self, notification: Notification) -> None:
        self.notification = notification

    @abstractmethod
    async def send_notification(self, recipient_user_id: int) -> None:
        raise NotImplementedError

    def generate_tasks(
        self,
        recipient_user_ids: list[int],
    ) -> Iterator[Awaitable[None]]:
        yield from (
            self.send_notification(recipient_user_id=recipient_user_id)
            for recipient_user_id in recipient_user_ids
        )
