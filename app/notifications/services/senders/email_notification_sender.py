from app.common.config_bdg import pochta_bridge
from app.common.schemas.pochta_sch import EmailMessageInputSchema
from app.notifications.models.delivery_methods_db import EmailDeliveryMethod
from app.notifications.models.notifications_db import Notification
from app.notifications.services.adapters.email_message_adapter import (
    NotificationToEmailMessageAdapter,
)
from app.notifications.services.senders.base_notification_sender import (
    BaseNotificationSender,
    session_lock,
)


class EmailNotificationSender(BaseNotificationSender):
    def __init__(self, notification: Notification) -> None:
        super().__init__(notification=notification)

        self.email_message_payload = NotificationToEmailMessageAdapter(
            notification=self.notification
        ).adapt()

    async def send_notification(self, recipient_user_id: int) -> None:
        async with session_lock:
            delivery_method = (
                await EmailDeliveryMethod.find_first_active_by_delivery_route(
                    user_id=recipient_user_id,
                    notification_category=self.notification_category,
                )
            )
        if delivery_method is None:
            return

        await pochta_bridge.send_email_message(
            EmailMessageInputSchema(
                payload=self.email_message_payload,
                recipient_emails=[delivery_method.email],
            )
        )
