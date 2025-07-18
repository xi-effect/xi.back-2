import pytest
from aiogram import Bot
from aiogram.types import ChatMemberMember
from faker import Faker

from app.common.dependencies.authorization_dep import ProxyAuthData
from app.notifications.models.telegram_connections_db import (
    TelegramConnection,
    TelegramConnectionStatus,
)
from app.notifications.services import telegram_connections_svc
from tests.common.active_session import ActiveSession
from tests.common.aiogram_factories import UserFactory
from tests.common.mock_stack import MockStack

pytestmark = pytest.mark.anyio


@pytest.mark.parametrize(
    "has_username_in_telegram",
    [
        pytest.param(True, id="with_username_in_telegram"),
        pytest.param(False, id="no_username_in_telegram"),
    ],
)
async def test_retrieving_telegram_username_by_user_id(
    faker: Faker,
    active_session: ActiveSession,
    mock_stack: MockStack,
    proxy_auth_data: ProxyAuthData,
    bot_id: int,
    bot: Bot,
    tg_chat_id: int,
    has_username_in_telegram: bool,
) -> None:
    async with active_session():
        await TelegramConnection.create(
            user_id=proxy_auth_data.user_id,
            chat_id=tg_chat_id,
            status=TelegramConnectionStatus.ACTIVE,
        )

    expected_new_username = faker.user_name() if has_username_in_telegram else None
    get_chat_member_mock = mock_stack.enter_async_mock(
        bot,
        "get_chat_member",
        return_value=ChatMemberMember(
            user=UserFactory.build(id=bot_id, username=expected_new_username),
        ),
    )

    async with active_session():
        new_username = (
            await telegram_connections_svc.retrieve_telegram_username_by_user_id(
                user_id=proxy_auth_data.user_id
            )
        )
        assert new_username == expected_new_username

    get_chat_member_mock.assert_awaited_once_with(
        chat_id=tg_chat_id,
        user_id=tg_chat_id,
    )

    async with active_session():
        await TelegramConnection.delete_by_kwargs(user_id=proxy_auth_data.user_id)


@pytest.mark.parametrize(
    "connection_status",
    [
        pytest.param(None, id="no_connection"),
        *(
            pytest.param(status, id=f"{status.value}_connection")
            for status in TelegramConnectionStatus
            if status is not TelegramConnectionStatus.ACTIVE
        ),
    ],
)
async def test_retrieving_telegram_username_by_user_id_connection_is_not_active(
    active_session: ActiveSession,
    proxy_auth_data: ProxyAuthData,
    tg_chat_id: int,
    connection_status: TelegramConnectionStatus | None,
) -> None:
    if connection_status is not None:
        async with active_session():
            await TelegramConnection.create(
                user_id=proxy_auth_data.user_id,
                chat_id=tg_chat_id,
                status=connection_status,
            )

    async with active_session():
        new_username = (
            await telegram_connections_svc.retrieve_telegram_username_by_user_id(
                user_id=proxy_auth_data.user_id
            )
        )
        assert new_username is None

    async with active_session():
        await TelegramConnection.delete_by_kwargs(user_id=proxy_auth_data.user_id)
