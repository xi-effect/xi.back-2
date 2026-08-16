import random
from collections.abc import AsyncIterator
from typing import cast
from uuid import UUID

import pytest
from faker import Faker
from respx import MockRouter, Route
from starlette.testclient import TestClient

from app.common.aiogram_ext import TelegramApp
from app.common.config import TelegramBotSettings, VKBotSettings, settings
from app.common.dependencies.authorization_dep import ProxyAuthData
from app.common.dependencies.telegram_auth_dep import TELEGRAM_WEBHOOK_TOKEN_HEADER_NAME
from app.common.schemas.notifications_sch import DeliveryMethodKind
from app.common.schemas.user_contacts_sch import UserContactKind
from app.notifications.config import telegram_app, vk_app
from app.notifications.models.delivery_methods_db import (
    DeliveryMethodStatus,
    EmailDeliveryMethod,
    TelegramDeliveryMethod,
    VKDeliveryMethod,
)
from app.notifications.models.disabled_delivery_routes_db import NotificationCategory
from app.notifications.models.notifications_db import Notification
from app.notifications.models.recipient_notifications_db import RecipientNotification
from app.notifications.models.user_contacts_db import UserContact
from app.notifications.utils.vk_app import VKApp
from app.notifications.utils.vk_client import VKClient
from tests.common.active_session import ActiveSession
from tests.common.aiogram_testing import (
    TelegramAppInitializer,
    TelegramBotWebhookDriver,
)
from tests.common.id_provider import IDProvider
from tests.common.mock_stack import MockStack
from tests.common.types import AnyJSON, PytestRequest
from tests.notifications import factories


@pytest.fixture()
async def classroom_id(faker: Faker) -> int:
    return faker.random_int()


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
    settings.telegram_notifications_bot = TelegramBotSettings(
        token=bot_token,
        webhook_token=notifications_bot_webhook_token,
    )
    return settings.telegram_notifications_bot


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


@pytest.fixture(scope="session")
def vk_notifications_bot_webhook_url() -> str:
    return "/api/public/notification-service/vk-updates/"


@pytest.fixture(scope="session")
def vk_notifications_bot_confirmation_code(faker: Faker) -> str:
    return faker.password(length=20, special_chars=False)


@pytest.fixture(scope="session")
def vk_notifications_bot_webhook_secret_key(faker: Faker) -> str:
    return faker.password(length=20, special_chars=False)


@pytest.fixture(scope="session", autouse=True)
def vk_notifications_bot_settings(
    faker: Faker,
    vk_notifications_bot_confirmation_code: str,
    vk_notifications_bot_webhook_secret_key: str,
) -> VKBotSettings:
    settings.vk_notifications_bot = VKBotSettings(
        api_token=faker.password(length=20, special_chars=False),
        confirmation_code=vk_notifications_bot_confirmation_code,
        webhook_secret_key=vk_notifications_bot_webhook_secret_key,
        group_id=faker.random_int(),
    )
    return settings.vk_notifications_bot


@pytest.fixture(autouse=True, scope="session")
async def initialized_vk_app(
    vk_notifications_bot_settings: VKBotSettings,
) -> AsyncIterator[VKApp]:
    async with VKClient(
        base_url=settings.vk_server_base_url,
        api_token=vk_notifications_bot_settings.api_token,
        group_id=vk_notifications_bot_settings.group_id,
    ) as vk_client:
        await vk_app.initialize(client=vk_client)
        yield vk_app


@pytest.fixture()
def vk_peer_id(id_provider: IDProvider) -> int:
    return id_provider.generate_id()


@pytest.fixture()
def vk_send_message_mock(faker: Faker, vk_respx_mock: MockRouter) -> Route:
    return vk_respx_mock.post(path="/messages.send").respond(
        json={"response": faker.random_int()}
    )


@pytest.fixture()
async def random_notification_category() -> NotificationCategory:
    # mypy gets confused, the real type is NotificationCategory
    return cast(NotificationCategory, random.choice(list(NotificationCategory)))


@pytest.fixture()
async def notification(active_session: ActiveSession) -> Notification:
    async with active_session():
        return await Notification.create(
            payload=factories.NotificationSimpleInputFactory.build().payload
        )


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
async def deleted_recipient_notification_id(
    active_session: ActiveSession, recipient_notification: RecipientNotification
) -> UUID:
    async with active_session():
        await recipient_notification.delete()
    return recipient_notification.notification_id


@pytest.fixture()
async def random_delivery_method_kind() -> DeliveryMethodKind:
    # mypy gets confused, the real type is DeliveryMethodKind
    return cast(DeliveryMethodKind, random.choice(list(DeliveryMethodKind)))


@pytest.fixture()
async def active_email_delivery_method(
    active_session: ActiveSession,
    proxy_auth_data: ProxyAuthData,
) -> AsyncIterator[EmailDeliveryMethod]:
    async with active_session():
        delivery_method = await EmailDeliveryMethod.create(
            user_id=proxy_auth_data.user_id,
            status=DeliveryMethodStatus.ACTIVE,
            **factories.EmailDeliveryMethodInputFactory.build_python(),
        )

    yield delivery_method

    async with active_session():
        await delivery_method.delete()


@pytest.fixture(
    params=[
        pytest.param(status, id=f"{status.value}_email")
        for status in DeliveryMethodStatus
        if status is not DeliveryMethodStatus.ACTIVE
    ]
)
async def inactive_email_delivery_method(
    active_session: ActiveSession,
    proxy_auth_data: ProxyAuthData,
    request: PytestRequest[DeliveryMethodStatus],
) -> AsyncIterator[EmailDeliveryMethod]:
    async with active_session():
        delivery_method = await EmailDeliveryMethod.create(
            user_id=proxy_auth_data.user_id,
            status=request.param,
            **factories.EmailDeliveryMethodInputFactory.build_python(),
        )

    yield delivery_method

    async with active_session():
        await delivery_method.delete()


@pytest.fixture(
    params=[
        pytest.param(status, id=f"{status.value}_email")
        for status in DeliveryMethodStatus
    ]
)
async def parametrized_email_delivery_method(
    active_session: ActiveSession,
    proxy_auth_data: ProxyAuthData,
    request: PytestRequest[DeliveryMethodStatus],
) -> AsyncIterator[EmailDeliveryMethod]:
    async with active_session():
        delivery_method = await EmailDeliveryMethod.create(
            user_id=proxy_auth_data.user_id,
            status=request.param,
            **factories.EmailDeliveryMethodInputFactory.build_python(),
        )

    yield delivery_method

    async with active_session():
        await delivery_method.delete()


@pytest.fixture()
async def active_telegram_delivery_method(
    active_session: ActiveSession,
    proxy_auth_data: ProxyAuthData,
    tg_chat_id: int,
) -> AsyncIterator[TelegramDeliveryMethod]:
    async with active_session():
        delivery_method = await TelegramDeliveryMethod.create(
            user_id=proxy_auth_data.user_id,
            peer_id=tg_chat_id,
            status=DeliveryMethodStatus.ACTIVE,
        )

    yield delivery_method

    async with active_session():
        await delivery_method.delete()


@pytest.fixture(
    params=[
        pytest.param(status, id=f"{status.value}_telegram")
        for status in DeliveryMethodStatus
        if status is not DeliveryMethodStatus.ACTIVE
    ]
)
async def inactive_telegram_delivery_method(
    active_session: ActiveSession,
    proxy_auth_data: ProxyAuthData,
    tg_chat_id: int,
    request: PytestRequest[DeliveryMethodStatus],
) -> AsyncIterator[TelegramDeliveryMethod]:
    async with active_session():
        delivery_method = await TelegramDeliveryMethod.create(
            user_id=proxy_auth_data.user_id,
            peer_id=tg_chat_id,
            status=request.param,
        )

    yield delivery_method

    async with active_session():
        await delivery_method.delete()


@pytest.fixture(
    params=[
        pytest.param(status, id=f"{status.value}_telegram")
        for status in DeliveryMethodStatus
    ]
)
async def parametrized_telegram_delivery_method(
    active_session: ActiveSession,
    proxy_auth_data: ProxyAuthData,
    tg_chat_id: int,
    request: PytestRequest[DeliveryMethodStatus],
) -> AsyncIterator[TelegramDeliveryMethod]:
    async with active_session():
        delivery_method = await TelegramDeliveryMethod.create(
            user_id=proxy_auth_data.user_id,
            peer_id=tg_chat_id,
            status=request.param,
        )

    yield delivery_method

    async with active_session():
        await TelegramDeliveryMethod.delete_by_kwargs(
            user_id=proxy_auth_data.user_id,
            kind=DeliveryMethodKind.TELEGRAM,
        )


@pytest.fixture()
async def active_vk_delivery_method(
    active_session: ActiveSession,
    proxy_auth_data: ProxyAuthData,
    vk_peer_id: int,
) -> AsyncIterator[VKDeliveryMethod]:
    async with active_session():
        delivery_method = await VKDeliveryMethod.create(
            user_id=proxy_auth_data.user_id,
            peer_id=vk_peer_id,
            status=DeliveryMethodStatus.ACTIVE,
        )

    yield delivery_method

    async with active_session():
        await VKDeliveryMethod.delete_by_kwargs(
            user_id=proxy_auth_data.user_id,
            kind=DeliveryMethodKind.VK,
        )


@pytest.fixture(
    params=[
        pytest.param(status, id=f"{status.value}_vk")
        for status in DeliveryMethodStatus
        if status is not DeliveryMethodStatus.ACTIVE
    ]
)
async def inactive_vk_delivery_method(
    active_session: ActiveSession,
    proxy_auth_data: ProxyAuthData,
    vk_peer_id: int,
    request: PytestRequest[DeliveryMethodStatus],
) -> AsyncIterator[VKDeliveryMethod]:
    async with active_session():
        delivery_method = await VKDeliveryMethod.create(
            user_id=proxy_auth_data.user_id,
            peer_id=vk_peer_id,
            status=request.param,
        )

    yield delivery_method

    async with active_session():
        await VKDeliveryMethod.delete_by_kwargs(
            user_id=proxy_auth_data.user_id,
            kind=DeliveryMethodKind.VK,
        )


@pytest.fixture(
    params=[
        pytest.param(status, id=f"{status.value}_vk") for status in DeliveryMethodStatus
    ]
)
async def parametrized_vk_delivery_method(
    active_session: ActiveSession,
    proxy_auth_data: ProxyAuthData,
    vk_peer_id: int,
    request: PytestRequest[DeliveryMethodStatus],
) -> AsyncIterator[VKDeliveryMethod]:
    async with active_session():
        delivery_method = await VKDeliveryMethod.create(
            user_id=proxy_auth_data.user_id,
            peer_id=vk_peer_id,
            status=request.param,
        )

    yield delivery_method

    async with active_session():
        await VKDeliveryMethod.delete_by_kwargs(
            user_id=proxy_auth_data.user_id,
            kind=DeliveryMethodKind.VK,
        )


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
async def personal_telegram_user_contact(
    active_session: ActiveSession,
    proxy_auth_data: ProxyAuthData,
) -> AsyncIterator[UserContact]:
    async with active_session():
        user_contact = await UserContact.create(
            user_id=proxy_auth_data.user_id,
            kind=UserContactKind.PERSONAL_TELEGRAM,
            **factories.UserContactInputFactory.build_python(),
        )

    yield user_contact

    async with active_session():
        await UserContact.delete_by_kwargs(
            user_id=proxy_auth_data.user_id,
            kind=UserContactKind.PERSONAL_TELEGRAM,
        )


@pytest.fixture()
async def personal_vk_user_contact(
    active_session: ActiveSession,
    proxy_auth_data: ProxyAuthData,
) -> AsyncIterator[UserContact]:
    async with active_session():
        user_contact = await UserContact.create(
            user_id=proxy_auth_data.user_id,
            kind=UserContactKind.PERSONAL_VK,
            **factories.UserContactInputFactory.build_python(),
        )

    yield user_contact

    async with active_session():
        await UserContact.delete_by_kwargs(
            user_id=proxy_auth_data.user_id,
            kind=UserContactKind.PERSONAL_VK,
        )


@pytest.fixture()
async def user_contact_data(user_contact: UserContact) -> AnyJSON:
    return UserContact.FullSchema.model_validate(
        user_contact, from_attributes=True
    ).model_dump(mode="json")
