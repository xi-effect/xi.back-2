import re

import pytest
from aiogram import Bot
from faker import Faker
from starlette.testclient import TestClient

from app.common.dependencies.authorization_dep import ProxyAuthData
from app.notifications.config import telegram_deep_link_provider
from tests.common.aiogram_factories import UserFactory
from tests.common.assert_contains_ext import assert_response
from tests.common.mock_stack import MockStack
from tests.notifications.constants import TELEGRAM_CONNECTION_LINK_PATTERN

pytestmark = pytest.mark.anyio


async def test_telegram_connection_link_generation(
    faker: Faker,
    mock_stack: MockStack,
    proxy_auth_data: ProxyAuthData,
    authorized_client: TestClient,
    bot: Bot,
) -> None:
    bot_username = faker.user_name()
    bot_me_mock = mock_stack.enter_async_mock(
        bot, "me", return_value=UserFactory.build(username=bot_username)
    )

    telegram_connection_link: str = assert_response(
        authorized_client.post(
            "/api/protected/notification-service/users/current/telegram-connection-requests/"
        ),
        expected_json=str,
    ).json()

    match = re.fullmatch(TELEGRAM_CONNECTION_LINK_PATTERN, telegram_connection_link)
    assert match is not None
    assert match.group("bot_username") == bot_username

    actual_decoded_user_id = (
        telegram_deep_link_provider.verify_and_decode_signed_link_payload(
            match.group("link_payload")
        )
    )
    assert actual_decoded_user_id == proxy_auth_data.user_id

    bot_me_mock.assert_awaited_once_with()
