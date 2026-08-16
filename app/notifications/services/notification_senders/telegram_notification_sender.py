from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.notifications.config import telegram_app
from app.notifications.models.delivery_methods_db import TelegramDeliveryMethod
from app.notifications.models.notifications_db import Notification
from app.notifications.services.notification_adapters.messenger_notification_adapter import (
    MessengerNotificationAdapter,
)
from app.notifications.services.notification_senders.base_notification_sender import (
    BaseNotificationSender,
    session_lock,
)


class TelegramNotificationSender(BaseNotificationSender):
    def __init__(self, notification: Notification) -> None:
        super().__init__(notification=notification)

        self.message_payload = MessengerNotificationAdapter(
            notification=self.notification
        ).adapt()

    async def send_notification(self, recipient_user_id: int) -> None:
        async with session_lock:
            delivery_method = (
                await TelegramDeliveryMethod.find_first_active_by_delivery_route(
                    user_id=recipient_user_id,
                    notification_category=self.notification_category,
                )
            )
        if delivery_method is None:
            return

        await telegram_app.bot.send_message(
            chat_id=delivery_method.peer_id,
            text=self.message_payload.message_text,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=self.message_payload.button_text,
                            url=self.message_payload.button_link,
                        )
                    ]
                ]
            ),
        )
