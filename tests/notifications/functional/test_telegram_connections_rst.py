import re

import pytest
from aiogram import Bot
from faker import Faker
from starlette import status
from starlette.testclient import TestClient

from app.common.dependencies.authorization_dep import ProxyAuthData
from app.notifications.config import telegram_deep_link_provider
from app.notifications.models.telegram_connections_db import TelegramConnection
from app.notifications.services import user_contacts_svc
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.mock_stack import MockStack
from tests.notifications.constants import TELEGRAM_CONNECTION_LINK_PATTERN

pytestmark = pytest.mark.anyio


async def test_telegram_connection_link_generation(
    faker: Faker,
    mock_stack: MockStack,
    proxy_auth_data: ProxyAuthData,
    authorized_client: TestClient,
    bot_username: str,
    bot: Bot,
) -> None:
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


@pytest.mark.usefixtures("telegram_connection")
async def test_telegram_connection_link_generation_telegram_connection_already_exists(
    authorized_client: TestClient,
) -> None:
    assert_response(
        authorized_client.post(
            "/api/protected/notification-service/users/current/telegram-connection-requests/"
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={"detail": "Telegram connection already exists"},
    )


@pytest.mark.usefixtures("telegram_connection")
async def test_telegram_connection_removing(
    active_session: ActiveSession,
    mock_stack: MockStack,
    proxy_auth_data: ProxyAuthData,
    authorized_client: TestClient,
) -> None:
    remove_personal_telegram_contact_mock = mock_stack.enter_async_mock(
        user_contacts_svc, "remove_personal_telegram_contact"
    )

    assert_nodata_response(
        authorized_client.delete(
            "/api/protected/notification-service/users/current/telegram-connection/"
        ),
    )

    remove_personal_telegram_contact_mock.assert_awaited_once_with(
        user_id=proxy_auth_data.user_id
    )

    async with active_session():
        assert (
            await TelegramConnection.find_first_by_id(proxy_auth_data.user_id)
        ) is None


async def test_telegram_connection_removing_telegram_connection_not_found(
    authorized_client: TestClient,
) -> None:
    assert_response(
        authorized_client.delete(
            "/api/protected/notification-service/users/current/telegram-connection/"
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Telegram connection not found"},
    )
