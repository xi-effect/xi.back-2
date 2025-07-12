import pytest
from aiogram.methods import SendMessage
from aiogram.types import Chat

from app.notifications import texts
from tests.common.aiogram_factories import MessageFactory, UpdateFactory, UserFactory
from tests.common.aiogram_testing import MockedBot, TelegramBotWebhookDriver

pytestmark = pytest.mark.anyio


async def test_starting(
    notifications_bot_webhook_driver: TelegramBotWebhookDriver,
    mocked_bot: MockedBot,
    tg_chat_id: int,
    tg_user_id: int,
) -> None:
    notifications_bot_webhook_driver.feed_update(
        UpdateFactory.build(
            message=MessageFactory.build(
                text="/start temp",
                chat=Chat(id=tg_chat_id, type="private"),
                from_user=UserFactory.build(id=tg_user_id),
            ),
        )
    )

    mocked_bot.assert_next_api_call(
        SendMessage,
        {
            "chat_id": tg_chat_id,
            "text": texts.WELCOME_MESSAGE,
            "reply_markup": None,
        },
    )
    mocked_bot.assert_next_api_call(
        SendMessage,
        {
            "chat_id": tg_chat_id,
            "text": "temp",
            "reply_markup": None,
        },
    )
    mocked_bot.assert_no_more_api_calls()
