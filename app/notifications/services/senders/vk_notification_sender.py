from app.notifications.config import vk_app
from app.notifications.models.delivery_methods_db import VKDeliveryMethod
from app.notifications.models.notifications_db import Notification
from app.notifications.schemas.vk.vk_messages_sch import (
    KeyboardButtonSchema,
    KeyboardLinkButtonActionSchema,
    KeyboardSchema,
    MessageSendInputSchema,
)
from app.notifications.services.adapters.messenger_notification_adapter import (
    MessengerNotificationAdapter,
)
from app.notifications.services.senders.base_notification_sender import (
    BaseNotificationSender,
    session_lock,
)


class VKNotificationSender(BaseNotificationSender):
    def __init__(self, notification: Notification) -> None:
        super().__init__(notification=notification)

        self.message_payload = MessengerNotificationAdapter(
            notification=self.notification
        ).adapt()

    async def send_notification(self, recipient_user_id: int) -> None:
        async with session_lock:
            delivery_method = (
                await VKDeliveryMethod.find_first_active_by_delivery_route(
                    user_id=recipient_user_id,
                    notification_category=self.notification_category,
                )
            )
        if delivery_method is None:
            return

        await vk_app.client.send_message(
            data=MessageSendInputSchema(
                peer_id=delivery_method.peer_id,
                message=self.message_payload.message_text,
                keyboard=KeyboardSchema(
                    inline=True,
                    buttons=[
                        [
                            KeyboardButtonSchema(
                                action=KeyboardLinkButtonActionSchema(
                                    link=self.message_payload.button_link,
                                    label=self.message_payload.button_text,
                                )
                            )
                        ]
                    ],
                ),
            ),
        )
