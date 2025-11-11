import random
from collections.abc import AsyncIterator
from typing import cast
from uuid import UUID

import pytest
from faker import Faker
from starlette.testclient import TestClient

from app.common.aiogram_ext import TelegramApp
from app.common.config import TelegramBotSettings, settings
from app.common.dependencies.authorization_dep import ProxyAuthData
from app.common.dependencies.telegram_auth_dep import TELEGRAM_WEBHOOK_TOKEN_HEADER_NAME
from app.common.schemas.user_contacts_sch import UserContactKind
from app.notifications.config import telegram_app
from app.notifications.models.email_connections_db import EmailConnection
from app.notifications.models.notifications_db import Notification
from app.notifications.models.recipient_notifications_db import RecipientNotification
from app.notifications.models.telegram_connections_db import (
    TelegramConnection,
    TelegramConnectionStatus,
)
from app.notifications.models.user_contacts_db import UserContact
from tests.common.active_session import ActiveSession
from tests.common.aiogram_testing import (
    TelegramAppInitializer,
    TelegramBotWebhookDriver,
)
from tests.common.mock_stack import MockStack
from tests.common.types import AnyJSON, PytestRequest
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
async def notification(active_session: ActiveSession) -> Notification:
    async with active_session():
        return await Notification.create(
            payload=factories.NotificationSimpleInputFactory.build().payload
        )


@pytest.fixture()
async def notification_data(notification: Notification) -> AnyJSON:
    return Notification.ResponseSchema.model_validate(
        notification, from_attributes=True
    ).model_dump(mode="json")


@pytest.fixture()
async def deleted_notification_id(
    active_session: ActiveSession, notification: Notification
) -> UUID:
    async with active_session():
        await notification.delete()
    return notification.id


@pytest.fixture()
async def recipient_notification(
    active_session: ActiveSession,
    authorized_user_id: int,
    notification: Notification,
) -> RecipientNotification:
    async with active_session():
        return await RecipientNotification.create(
            notification=notification,
            recipient_user_id=authorized_user_id,
        )


@pytest.fixture()
async def recipient_notification_data(
    recipient_notification: RecipientNotification,
) -> AnyJSON:
    return RecipientNotification.ResponseSchema.model_validate(
        recipient_notification, from_attributes=True
    ).model_dump(mode="json")


@pytest.fixture()
async def deleted_recipient_notification_id(
    active_session: ActiveSession, recipient_notification: RecipientNotification
) -> UUID:
    async with active_session():
        await recipient_notification.delete()
    return recipient_notification.notification_id


@pytest.fixture()
async def email_connection(
    active_session: ActiveSession,
    authorized_user_id: int,
) -> AsyncIterator[EmailConnection]:
    async with active_session():
        email_connection = await EmailConnection.create(
            user_id=authorized_user_id,
            **factories.EmailConnectionInputFactory.build_python(),
        )

    yield email_connection

    async with active_session():
        await email_connection.delete()


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
        await telegram_connection.delete()


@pytest.fixture()
async def active_telegram_connection(
    active_session: ActiveSession,
    proxy_auth_data: ProxyAuthData,
    tg_chat_id: int,
) -> AsyncIterator[TelegramConnection]:
    async with active_session():
        telegram_connection = await TelegramConnection.create(
            user_id=proxy_auth_data.user_id,
            chat_id=tg_chat_id,
            status=TelegramConnectionStatus.ACTIVE,
        )

    yield telegram_connection

    async with active_session():
        await telegram_connection.delete()


@pytest.fixture(
    params=[
        pytest.param(status, id=f"{status.value}_connection")
        for status in TelegramConnectionStatus
        if status is not TelegramConnectionStatus.ACTIVE
    ]
)
async def inactive_telegram_connection(
    active_session: ActiveSession,
    proxy_auth_data: ProxyAuthData,
    tg_chat_id: int,
    request: PytestRequest[TelegramConnection],
) -> AsyncIterator[TelegramConnection]:
    async with active_session():
        telegram_connection = await TelegramConnection.create(
            user_id=proxy_auth_data.user_id,
            chat_id=tg_chat_id,
            status=request.param,
        )

    yield telegram_connection

    async with active_session():
        await telegram_connection.delete()


@pytest.fixture()
def telegram_connection_data(telegram_connection: TelegramConnection) -> AnyJSON:
    return TelegramConnection.ResponseMUBSchema.model_validate(
        telegram_connection, from_attributes=True
    ).model_dump(mode="json")


@pytest.fixture()
def random_contact_kind() -> UserContactKind:
    # mypy gets confused, the real type is UserContactKind
    return cast(UserContactKind, random.choice(list(UserContactKind)))


@pytest.fixture()
async def user_contact(
    active_session: ActiveSession,
    proxy_auth_data: ProxyAuthData,
    random_contact_kind: UserContactKind,
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
