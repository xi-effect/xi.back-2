import pytest
from aiogram import Bot
from aiogram.types import ChatMemberMember
from faker import Faker

from app.common.dependencies.authorization_dep import ProxyAuthData
from app.notifications.models.telegram_connections_db import TelegramConnection
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
    active_telegram_connection: TelegramConnection,
    has_username_in_telegram: bool,
) -> None:
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


async def test_retrieving_telegram_username_by_user_id_connection_is_not_active(
    active_session: ActiveSession,
    proxy_auth_data: ProxyAuthData,
    tg_chat_id: int,
    inactive_telegram_connection: TelegramConnection,
) -> None:
    async with active_session():
        new_username = (
            await telegram_connections_svc.retrieve_telegram_username_by_user_id(
                user_id=proxy_auth_data.user_id
            )
        )
        assert new_username is None
