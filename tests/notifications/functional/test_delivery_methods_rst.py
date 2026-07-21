import re

import pytest
from aiogram import Bot
from faker import Faker
from pytest_lazy_fixtures import lf
from starlette import status
from starlette.testclient import TestClient

from app.common.dependencies.authorization_dep import ProxyAuthData
from app.common.schemas.notifications_sch import DeliveryMethodKind
from app.notifications.config import telegram_deep_link_provider
from app.notifications.models.delivery_methods_db import (
    DeliveryMethod,
    TelegramDeliveryMethod,
)
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
            "/api/protected/notification-service/users/current"
            f"/delivery-methods/{DeliveryMethodKind.TELEGRAM}/connection-requests/"
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


@pytest.mark.usefixtures("parametrized_telegram_delivery_method")
async def test_telegram_connection_link_generation_delivery_method_already_exists(
    authorized_client: TestClient,
) -> None:
    assert_response(
        authorized_client.post(
            "/api/protected/notification-service/users/current"
            f"/delivery-methods/{DeliveryMethodKind.TELEGRAM}/connection-requests/"
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={"detail": "Delivery method already exists"},
    )


@pytest.mark.parametrize(
    "delivery_method",
    [
        pytest.param(lf("parametrized_telegram_delivery_method"), id="telegram"),
        pytest.param(lf("parametrized_vk_delivery_method"), id="vk"),
    ],
)
async def test_delivery_method_removing(
    active_session: ActiveSession,
    mock_stack: MockStack,
    proxy_auth_data: ProxyAuthData,
    authorized_client: TestClient,
    delivery_method: DeliveryMethod,
) -> None:
    remove_personal_telegram_contact_mock = mock_stack.enter_async_mock(
        user_contacts_svc, "remove_personal_telegram_contact"
    )

    assert_nodata_response(
        authorized_client.delete(
            "/api/protected/notification-service/users/current"
            f"/delivery-methods/{delivery_method.kind}/"
        ),
    )

    if isinstance(delivery_method, TelegramDeliveryMethod):
        remove_personal_telegram_contact_mock.assert_awaited_once_with(
            user_id=proxy_auth_data.user_id
        )
    else:
        remove_personal_telegram_contact_mock.assert_not_called()

    async with active_session():
        assert (
            await DeliveryMethod.find_first_by_primary_key(
                user_id=proxy_auth_data.user_id,
                kind=delivery_method.kind,
            )
        ) is None


@pytest.mark.parametrize(
    "delivery_method_kind",
    [
        pytest.param(DeliveryMethodKind.TELEGRAM, id="telegram"),
        pytest.param(DeliveryMethodKind.VK, id="vk"),
    ],
)
async def test_delivery_method_removing_delivery_method_not_found(
    authorized_client: TestClient,
    delivery_method_kind: DeliveryMethodKind,
) -> None:
    assert_response(
        authorized_client.delete(
            "/api/protected/notification-service/users/current"
            f"/delivery-methods/{delivery_method_kind}/"
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Delivery method not found"},
    )
