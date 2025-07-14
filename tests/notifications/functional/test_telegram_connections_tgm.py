import random

import pytest
from aiogram.methods import SendMessage
from aiogram.types import Chat
from faker import Faker
from pydantic_marshals.contains import assert_contains

from app.common.dependencies.authorization_dep import ProxyAuthData
from app.notifications import texts
from app.notifications.config import telegram_deep_link_provider
from app.notifications.models.telegram_connections_db import (
    TelegramConnection,
    TelegramConnectionStatus,
)
from tests.common.active_session import ActiveSession
from tests.common.aiogram_factories import MessageFactory, UpdateFactory, UserFactory
from tests.common.aiogram_testing import MockedBot, TelegramBotWebhookDriver
from tests.common.id_provider import IDProvider

pytestmark = pytest.mark.anyio


@pytest.mark.parametrize(
    ("other_connection_status", "expected_reply_text"),
    [
        pytest.param(
            None,
            texts.NOTIFICATIONS_CONNECTED_MESSAGE,
            id="no_other_connections",
        ),
        pytest.param(
            TelegramConnectionStatus.REPLACED,
            texts.NOTIFICATIONS_CONNECTED_MESSAGE,
            id="replaced_other_connection",
        ),
        pytest.param(
            TelegramConnectionStatus.ACTIVE,
            texts.NOTIFICATIONS_REPLACES_MESSAGE,
            id="active_other_connection",
        ),
        pytest.param(
            TelegramConnectionStatus.BLOCKED,
            texts.NOTIFICATIONS_REPLACES_MESSAGE,
            id="blocked_other_connection",
        ),
    ],
)
async def test_telegram_connection_creating(
    active_session: ActiveSession,
    id_provider: IDProvider,
    proxy_auth_data: ProxyAuthData,
    notifications_bot_webhook_driver: TelegramBotWebhookDriver,
    mocked_bot: MockedBot,
    tg_chat_id: int,
    tg_user_id: int,
    other_connection_status: TelegramConnectionStatus | None,
    expected_reply_text: str,
) -> None:
    if other_connection_status is not None:
        async with active_session():
            other_telegram_connection = await TelegramConnection.create(
                user_id=id_provider.generate_id(),
                chat_id=tg_chat_id,
                status=other_connection_status,
            )

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

    async with active_session() as session:
        telegram_connection = await TelegramConnection.find_first_by_id(
            proxy_auth_data.user_id
        )
        assert telegram_connection is not None
        assert_contains(
            telegram_connection,
            {
                "chat_id": tg_chat_id,
                "status": TelegramConnectionStatus.ACTIVE,
            },
        )
        await telegram_connection.delete()

        if other_connection_status is not None:
            session.add(other_telegram_connection)
            await session.refresh(other_telegram_connection)
            assert other_telegram_connection.status is TelegramConnectionStatus.REPLACED
            await other_telegram_connection.delete()

    mocked_bot.assert_next_api_call(
        SendMessage,
        {
            "chat_id": tg_chat_id,
            "text": expected_reply_text,
            "reply_markup": None,
        },
    )
    mocked_bot.assert_no_more_api_calls()


@pytest.mark.parametrize(
    ("has_same_chat_id", "expected_reply_text"),
    [
        pytest.param(
            True,
            texts.NOTIFICATIONS_ALREADY_CONNECTED_MESSAGE,
            id="same_chat",
        ),
        pytest.param(
            False,
            texts.TOKEN_ALREADY_USED_MESSAGE,
            id="different_chat",
        ),
    ],
)
async def test_telegram_connection_creating_telegram_connection_already_exists(
    active_session: ActiveSession,
    id_provider: IDProvider,
    proxy_auth_data: ProxyAuthData,
    notifications_bot_webhook_driver: TelegramBotWebhookDriver,
    mocked_bot: MockedBot,
    tg_chat_id: int,
    tg_user_id: int,
    has_same_chat_id: bool,
    expected_reply_text: str,
) -> None:
    async with active_session():
        await TelegramConnection.create(
            user_id=proxy_auth_data.user_id,
            chat_id=tg_chat_id if has_same_chat_id else id_provider.generate_id(),
            status=random.choice(list(TelegramConnectionStatus)),
        )

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

    async with active_session():
        await TelegramConnection.delete_by_kwargs(user_id=proxy_auth_data.user_id)

    mocked_bot.assert_next_api_call(
        SendMessage,
        {
            "chat_id": tg_chat_id,
            "text": expected_reply_text,
            "reply_markup": None,
        },
    )
    mocked_bot.assert_no_more_api_calls()


async def test_telegram_connection_creating_invalid_token(
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
