from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.notifications.config import telegram_app
from app.notifications.models.notifications_db import Notification
from app.notifications.models.telegram_connections_db import (
    TelegramConnection,
    TelegramConnectionStatus,
)
from app.notifications.services.adapters.telegram_message_adapter import (
    NotificationToTelegramMessageAdapter,
)
from app.notifications.services.senders.base_notification_sender import (
    BaseNotificationSender,
)


class TelegramNotificationSender(BaseNotificationSender):
    def __init__(self, notification: Notification) -> None:
        super().__init__(notification=notification)

        self.telegram_message_payload = NotificationToTelegramMessageAdapter(
            notification=self.notification
        ).adapt()

    async def send_notification(self, recipient_user_id: int) -> None:
        telegram_connection = await TelegramConnection.find_first_by_user_id_and_status(
            user_id=recipient_user_id,
            allowed_statuses=[TelegramConnectionStatus.ACTIVE],
        )
        if telegram_connection is None:
            return

        await telegram_app.bot.send_message(
            chat_id=telegram_connection.chat_id,
            text=self.telegram_message_payload.message_text,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=self.telegram_message_payload.button_text,
                            url=self.telegram_message_payload.button_link,
                        )
                    ]
                ]
            ),
        )
