import pytest
from aiogram.methods import SendMessage
from aiogram.types import Chat
from faker import Faker

from app.common.dependencies.authorization_dep import ProxyAuthData
from app.notifications import texts
from app.notifications.config import telegram_deep_link_provider
from tests.common.aiogram_factories import MessageFactory, UpdateFactory, UserFactory
from tests.common.aiogram_testing import MockedBot, TelegramBotWebhookDriver

pytestmark = pytest.mark.anyio


async def test_starting_with_deep_link(
    proxy_auth_data: ProxyAuthData,
    notifications_bot_webhook_driver: TelegramBotWebhookDriver,
    mocked_bot: MockedBot,
    tg_chat_id: int,
    tg_user_id: int,
) -> None:
    signed_deep_link_content = telegram_deep_link_provider.create_signed_link_payload(
        user_id=proxy_auth_data.user_id
    )

    notifications_bot_webhook_driver.feed_update(
        UpdateFactory.build(
            message=MessageFactory.build(
                text=f"/start {signed_deep_link_content}",
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
            "text": str(proxy_auth_data.user_id),
            "reply_markup": None,
        },
    )
    mocked_bot.assert_no_more_api_calls()


async def test_starting_with_deep_link_invalid_token(
    faker: Faker,
    notifications_bot_webhook_driver: TelegramBotWebhookDriver,
    mocked_bot: MockedBot,
    tg_chat_id: int,
    tg_user_id: int,
) -> None:
    # Basic case to verify error handling. Specific cases are tested in unit/test_deep_links

    notifications_bot_webhook_driver.feed_update(
        UpdateFactory.build(
            message=MessageFactory.build(
                text=f"/start {faker.pystr()}",
                chat=Chat(id=tg_chat_id, type="private"),
                from_user=UserFactory.build(id=tg_user_id),
            ),
        )
    )

    mocked_bot.assert_next_api_call(
        SendMessage,
        {
            "chat_id": tg_chat_id,
            "text": texts.INVALID_TOKEN_MESSAGE,
            "reply_markup": None,
        },
    )
    mocked_bot.assert_no_more_api_calls()
