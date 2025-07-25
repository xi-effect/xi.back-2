import random
from collections.abc import AsyncIterator
from typing import cast

import pytest
from faker import Faker
from starlette.testclient import TestClient

from app.common.aiogram_ext import TelegramApp
from app.common.config import TelegramBotSettings, settings
from app.common.dependencies.authorization_dep import ProxyAuthData
from app.common.dependencies.telegram_auth_dep import TELEGRAM_WEBHOOK_TOKEN_HEADER_NAME
from app.notifications.config import telegram_app
from app.notifications.models.telegram_connections_db import (
    TelegramConnection,
    TelegramConnectionStatus,
)
from app.notifications.models.user_contacts_db import ContactKind, UserContact
from tests.common.active_session import ActiveSession
from tests.common.aiogram_testing import (
    TelegramAppInitializer,
    TelegramBotWebhookDriver,
)
from tests.common.mock_stack import MockStack
from tests.common.types import AnyJSON
from tests.notifications import factories


@pytest.fixture(scope="session")
def notifications_bot_webhook_url() -> str:
    return "/api/public/notification-service/telegram-updates/"


@pytest.fixture(scope="session")
def notifications_bot_webhook_token(faker: Faker) -> str:
    return faker.password(length=20, special_chars=False)


@pytest.fixture(scope="session", autouse=True)
def notifications_bot_settings(
    mock_stack_session: MockStack,
    bot_token: str,
    notifications_bot_webhook_token: str,
) -> TelegramBotSettings:
    settings.notifications_bot = TelegramBotSettings(
        token=bot_token,
        webhook_token=notifications_bot_webhook_token,
    )
    return settings.notifications_bot


@pytest.fixture(scope="session")
def notifications_bot_webhook_driver(
    client: TestClient,
    notifications_bot_webhook_url: str,
    notifications_bot_webhook_token: str,
) -> TelegramBotWebhookDriver:
    return TelegramBotWebhookDriver(
        client=TestClient(
            client.app,
            headers={
                TELEGRAM_WEBHOOK_TOKEN_HEADER_NAME: notifications_bot_webhook_token
            },
        ),
        webhook_url=notifications_bot_webhook_url,
    )


@pytest.fixture(autouse=True, scope="session")
def initialized_telegram_app(
    initialize_telegram_app: TelegramAppInitializer,
) -> TelegramApp:
    return initialize_telegram_app(
        telegram_app=telegram_app,
    )


@pytest.fixture()
def random_telegram_connection_status() -> TelegramConnectionStatus:
    # mypy gets confused, the real type is TelegramConnectionStatus
    return cast(TelegramConnectionStatus, random.choice(list(TelegramConnectionStatus)))


@pytest.fixture()
async def telegram_connection(
    active_session: ActiveSession,
    proxy_auth_data: ProxyAuthData,
    tg_chat_id: int,
    random_telegram_connection_status: TelegramConnectionStatus,
) -> AsyncIterator[TelegramConnection]:
    async with active_session():
        telegram_connection = await TelegramConnection.create(
            user_id=proxy_auth_data.user_id,
            chat_id=tg_chat_id,
            status=random_telegram_connection_status,
        )

    yield telegram_connection

    async with active_session():
        await TelegramConnection.delete_by_kwargs(user_id=proxy_auth_data.user_id)


@pytest.fixture()
def telegram_connection_data(telegram_connection: TelegramConnection) -> AnyJSON:
    return TelegramConnection.ResponseMUBSchema.model_validate(
        telegram_connection, from_attributes=True
    ).model_dump(mode="json")


@pytest.fixture()
def random_contact_kind() -> ContactKind:
    # mypy gets confused, the real type is ContactKind
    return cast(ContactKind, random.choice(list(ContactKind)))


@pytest.fixture()
async def user_contact(
    active_session: ActiveSession,
    proxy_auth_data: ProxyAuthData,
    random_contact_kind: ContactKind,
) -> AsyncIterator[UserContact]:
    async with active_session():
        user_contact = await UserContact.create(
            user_id=proxy_auth_data.user_id,
            kind=random_contact_kind,
            **factories.UserContactInputFactory.build_python(),
        )

    yield user_contact

    async with active_session():
        await UserContact.delete_by_kwargs(
            user_id=proxy_auth_data.user_id,
            kind=random_contact_kind,
        )


@pytest.fixture()
async def user_contact_data(user_contact: UserContact) -> AnyJSON:
    return UserContact.FullSchema.model_validate(
        user_contact, from_attributes=True
    ).model_dump(mode="json")
