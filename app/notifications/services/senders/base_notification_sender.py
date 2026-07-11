from abc import ABC, abstractmethod
from collections.abc import Awaitable, Iterator

from app.common.schemas.notifications_sch import NotificationKind
from app.notifications.models.disabled_delivery_routes_db import NotificationCategory
from app.notifications.models.notifications_db import Notification

NOTIFICATION_KIND_TO_NOTIFICATION_CATEGORY: dict[
    NotificationKind, NotificationCategory | None
] = {
    NotificationKind.INDIVIDUAL_INVITATION_ACCEPTED_V1: NotificationCategory.CLASSROOMS,
    NotificationKind.GROUP_INVITATION_ACCEPTED_V1: NotificationCategory.CLASSROOMS,
    NotificationKind.ENROLLMENT_CREATED_V1: NotificationCategory.CLASSROOMS,
    NotificationKind.CLASSROOM_CONFERENCE_STARTED_V1: NotificationCategory.CLASSROOMS,
    NotificationKind.RECIPIENT_INVOICE_CREATED_V1: NotificationCategory.INVOICES,
    NotificationKind.STUDENT_RECIPIENT_INVOICE_PAYMENT_CONFIRMED_V1: NotificationCategory.INVOICES,
    NotificationKind.SINGLE_CLASSROOM_EVENT_CREATED_V1: NotificationCategory.EVENTS,
    NotificationKind.CLASSROOM_EVENT_INSTANCE_RESCHEDULED_V1: NotificationCategory.EVENTS,
    NotificationKind.CLASSROOM_EVENT_INSTANCE_CANCELLED_V1: NotificationCategory.EVENTS,
    NotificationKind.REPEATING_CLASSROOM_EVENT_CREATED_V1: NotificationCategory.EVENTS,
    NotificationKind.CLASSROOM_EVENT_REPETITION_UPDATED_V1: NotificationCategory.EVENTS,
    NotificationKind.CLASSROOM_EVENT_REPETITION_CANCELLED_V1: NotificationCategory.EVENTS,
    NotificationKind.PERSISTED_CLASSROOM_EVENT_INSTANCE_REMINDER_V1: NotificationCategory.EVENT_REMINDERS,
    NotificationKind.REPEATED_CLASSROOM_EVENT_INSTANCE_REMINDER_V1: NotificationCategory.EVENT_REMINDERS,
    NotificationKind.CUSTOM_V1: None,
}


class BaseNotificationSender(ABC):
    def __init__(self, notification: Notification) -> None:
        self.notification = notification

    @property
    def notification_category(self) -> NotificationCategory | None:
        return NOTIFICATION_KIND_TO_NOTIFICATION_CATEGORY[
            self.notification.payload.kind
        ]

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
