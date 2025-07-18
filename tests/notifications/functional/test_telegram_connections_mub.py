import re
from typing import Any

import pytest
from aiogram import Bot
from aiogram.methods import SendMessage
from faker import Faker
from starlette import status
from starlette.testclient import TestClient

from app.common.dependencies.authorization_dep import ProxyAuthData
from app.notifications.config import telegram_deep_link_provider
from app.notifications.models.telegram_connections_db import (
    TelegramConnection,
    TelegramConnectionStatus,
)
from app.notifications.routes.telegram_connections_mub import TelegramMessageSchema
from tests.common.active_session import ActiveSession
from tests.common.aiogram_testing import MockedBot
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.mock_stack import MockStack
from tests.common.polyfactory_ext import BaseModelFactory
from tests.common.types import AnyJSON
from tests.notifications.constants import TELEGRAM_CONNECTION_LINK_PATTERN
from tests.notifications.factories import (
    TelegramConnectionInputMUBFactory,
    TelegramConnectionPatchMUBFactory,
    TelegramMessageFactory,
)

pytestmark = pytest.mark.anyio


async def test_telegram_connection_link_generation(
    faker: Faker,
    mock_stack: MockStack,
    mub_client: TestClient,
    proxy_auth_data: ProxyAuthData,
    bot_username: str,
    bot: Bot,
) -> None:
    telegram_connection_link: str = assert_response(
        mub_client.post(
            f"/mub/notification-service/users/{proxy_auth_data.user_id}/telegram-connection-requests/"
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


async def test_telegram_connection_creation(
    active_session: ActiveSession,
    mub_client: TestClient,
    proxy_auth_data: ProxyAuthData,
) -> None:
    input_data = TelegramConnectionInputMUBFactory.build_json()

    assert_response(
        mub_client.post(
            f"/mub/notification-service/users/{proxy_auth_data.user_id}/telegram-connection/",
            json=input_data,
        ),
        expected_code=status.HTTP_201_CREATED,
        expected_json={**input_data},
    )

    async with active_session():
        telegram_connection = await TelegramConnection.find_first_by_id(
            proxy_auth_data.user_id
        )
        assert telegram_connection is not None
        await telegram_connection.delete()


@pytest.mark.parametrize(
    "path",
    [
        pytest.param("/telegram-connection-requests/", id="generate_link"),
        pytest.param("/telegram-connection/", id="create"),
    ],
)
@pytest.mark.usefixtures("telegram_connection")
async def test_telegram_connection_already_existing(
    mub_client: TestClient,
    proxy_auth_data: ProxyAuthData,
    path: str,
) -> None:
    assert_response(
        mub_client.post(
            f"/mub/notification-service/users/{proxy_auth_data.user_id}{path}",
            json=TelegramConnectionInputMUBFactory.build_json(),
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={"detail": "Telegram connection already exists"},
    )


async def test_telegram_connection_retrieving(
    mub_client: TestClient,
    telegram_connection: TelegramConnection,
    telegram_connection_data: AnyJSON,
) -> None:
    assert_response(
        mub_client.get(
            f"/mub/notification-service/users/{telegram_connection.user_id}/telegram-connection/",
        ),
        expected_json=telegram_connection_data,
    )


async def test_telegram_connection_updating(
    mub_client: TestClient,
    telegram_connection: TelegramConnection,
    telegram_connection_data: AnyJSON,
) -> None:
    input_data = TelegramConnectionPatchMUBFactory.build_json()
    assert_response(
        mub_client.patch(
            f"/mub/notification-service/users/{telegram_connection.user_id}/telegram-connection/",
            json=input_data,
        ),
        expected_json={**input_data, **telegram_connection_data},
    )


async def test_telegram_connection_deleting(
    active_session: ActiveSession,
    mub_client: TestClient,
    telegram_connection: TelegramConnection,
) -> None:
    assert_nodata_response(
        mub_client.delete(
            f"/mub/notification-service/users/{telegram_connection.user_id}/telegram-connection/",
        )
    )

    async with active_session():
        assert (
            await TelegramConnection.find_first_by_id(telegram_connection.user_id)
            is None
        )


async def test_sending_message_to_user_via_telegram(
    active_session: ActiveSession,
    mub_client: TestClient,
    proxy_auth_data: ProxyAuthData,
    mocked_bot: MockedBot,
    tg_chat_id: int,
) -> None:
    async with active_session():
        await TelegramConnection.create(
            user_id=proxy_auth_data.user_id,
            chat_id=tg_chat_id,
            status=TelegramConnectionStatus.ACTIVE,
        )

    message_data: AnyJSON = TelegramMessageFactory.build_json()

    assert_nodata_response(
        mub_client.post(
            f"/mub/notification-service/users/{proxy_auth_data.user_id}/telegram-connection/messages/",
            json=message_data,
        ),
    )

    mocked_bot.assert_next_api_call(
        SendMessage,
        {
            **message_data,
            "chat_id": tg_chat_id,
            "reply_markup": None,
        },
    )
    mocked_bot.assert_no_more_api_calls()


@pytest.mark.parametrize(
    "connection_status",
    [
        pytest.param(status, id=f"{status.value}_connection")
        for status in TelegramConnectionStatus
        if status is not TelegramConnectionStatus.ACTIVE
    ],
)
async def test_sending_message_to_user_via_telegram_connection_is_not_active(
    active_session: ActiveSession,
    mub_client: TestClient,
    proxy_auth_data: ProxyAuthData,
    mocked_bot: MockedBot,
    tg_chat_id: int,
    connection_status: TelegramConnectionStatus,
) -> None:
    async with active_session():
        await TelegramConnection.create(
            user_id=proxy_auth_data.user_id,
            chat_id=tg_chat_id,
            status=connection_status,
        )

    message_data: TelegramMessageSchema = TelegramMessageFactory.build()

    assert_response(
        mub_client.post(
            f"/mub/notification-service/users/{proxy_auth_data.user_id}/telegram-connection/messages/",
            json=message_data.model_dump(mode="json"),
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={"detail": "Telegram connection is not active"},
    )

    mocked_bot.assert_no_more_api_calls()


@pytest.mark.parametrize(
    ("method", "path", "body_factory"),
    [
        pytest.param("GET", "/", None, id="retrieve"),
        pytest.param("PATCH", "/", TelegramConnectionPatchMUBFactory, id="update"),
        pytest.param("DELETE", "/", None, id="delete"),
        pytest.param("POST", "/messages/", TelegramMessageFactory, id="send-message"),
    ],
)
async def test_telegram_connection_not_finding(
    active_session: ActiveSession,
    mub_client: TestClient,
    proxy_auth_data: ProxyAuthData,
    method: str,
    path: str,
    body_factory: type[BaseModelFactory[Any]] | None,
) -> None:
    assert_response(
        mub_client.request(
            method=method,
            url=f"/mub/notification-service/users/{proxy_auth_data.user_id}/telegram-connection{path}",
            json=body_factory and body_factory.build_json(),
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Telegram connection not found"},
    )
