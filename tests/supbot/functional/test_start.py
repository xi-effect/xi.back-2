import pytest
from aiogram.methods import SendMessage
from aiogram.types import Chat

from app.supbot import texts
from tests.common.aiogram_factories import MessageFactory, UpdateFactory, UserFactory
from tests.common.aiogram_testing import MockedBot, TelegramBotWebhookDriver
from tests.supbot.conftest import EXPECTED_MAIN_MENU_KEYBOARD_MARKUP

pytestmark = pytest.mark.anyio


async def test_starting(
    supbot_webhook_driver: TelegramBotWebhookDriver,
    mocked_bot: MockedBot,
    tg_chat_id: int,
    tg_user_id: int,
) -> None:
    supbot_webhook_driver.feed_update(
        UpdateFactory.build(
            message=MessageFactory.build(
                text="/start",
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
            "reply_markup": EXPECTED_MAIN_MENU_KEYBOARD_MARKUP,
        },
    )
    mocked_bot.assert_no_more_api_calls()
