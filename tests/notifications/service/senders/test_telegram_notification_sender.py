import pytest
from aiogram.methods import SendMessage

from app.notifications.models.notifications_db import Notification
from app.notifications.models.telegram_connections_db import (
    TelegramConnection,
)
from app.notifications.services.senders.telegram_notification_sender import (
    TelegramNotificationSender,
)
from tests.common.active_session import ActiveSession
from tests.common.aiogram_testing import MockedBot

pytestmark = pytest.mark.anyio


@pytest.fixture()
async def telegram_notification_sender(
    notification: Notification,
) -> TelegramNotificationSender:
    return TelegramNotificationSender(notification=notification)


async def test_telegram_notification_sending(
    active_session: ActiveSession,
    authorized_user_id: int,
    mocked_bot: MockedBot,
    tg_chat_id: int,
    active_telegram_connection: TelegramConnection,
    telegram_notification_sender: TelegramNotificationSender,
) -> None:
    async with active_session():
        await telegram_notification_sender.send_notification(
            recipient_user_id=authorized_user_id
        )

    mocked_bot.assert_next_api_call(
        SendMessage,
        {
            "chat_id": tg_chat_id,
            "text": telegram_notification_sender.telegram_message_payload.message_text,
            "reply_markup": {
                "inline_keyboard": [
                    [
                        {
                            "text": telegram_notification_sender.telegram_message_payload.button_text,
                            "url": telegram_notification_sender.telegram_message_payload.button_link,
                        }
                    ]
                ]
            },
        },
    )
    mocked_bot.assert_no_more_api_calls()


async def test_telegram_notification_sending_connection_is_not_active(
    active_session: ActiveSession,
    authorized_user_id: int,
    mocked_bot: MockedBot,
    inactive_telegram_connection: TelegramConnection,
    telegram_notification_sender: TelegramNotificationSender,
) -> None:
    async with active_session():
        await telegram_notification_sender.send_notification(
            recipient_user_id=authorized_user_id
        )

    mocked_bot.assert_no_more_api_calls()


async def test_telegram_notification_sending_telegram_connection_not_found(
    active_session: ActiveSession,
    authorized_user_id: int,
    mocked_bot: MockedBot,
    telegram_notification_sender: TelegramNotificationSender,
) -> None:
    async with active_session():
        await telegram_notification_sender.send_notification(
            recipient_user_id=authorized_user_id
        )

    mocked_bot.assert_no_more_api_calls()
