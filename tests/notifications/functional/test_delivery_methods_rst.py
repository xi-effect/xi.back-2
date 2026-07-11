import re

import pytest
from aiogram import Bot
from faker import Faker
from pydantic_marshals.contains import TypeChecker
from pytest_lazy_fixtures import lfc
from starlette import status
from starlette.testclient import TestClient

from app.common.dependencies.authorization_dep import ProxyAuthData
from app.common.schemas.notifications_sch import DeliveryMethodKind
from app.notifications.config import telegram_deep_link_provider
from app.notifications.models.delivery_methods_db import (
    EmailDeliveryMethod,
    TelegramDeliveryMethod,
)
from app.notifications.models.user_contacts_db import UserContact
from app.notifications.services import user_contacts_svc
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.mock_stack import MockStack
from tests.common.utils import repackage_json
from tests.notifications.constants import TELEGRAM_CONNECTION_LINK_PATTERN

pytestmark = pytest.mark.anyio


@pytest.mark.parametrize(
    "expected_email_delivery_method_data",
    [
        pytest.param(None, id="no_email"),
        pytest.param(
            lfc(
                lambda parametrized_email_delivery_method: {
                    "delivery_method": repackage_json(
                        EmailDeliveryMethod.ResponseSchema,
                        parametrized_email_delivery_method,
                    ),
                    "related_contact": None,
                }
            ),
            id="with_email",
        ),
    ],
)
@pytest.mark.parametrize(
    "expected_telegram_delivery_method_data",
    [
        pytest.param(None, id="no_telegram"),
        pytest.param(
            lfc(
                lambda parametrized_telegram_delivery_method: {
                    "delivery_method": repackage_json(
                        TelegramDeliveryMethod.ResponseSchema,
                        parametrized_telegram_delivery_method,
                    ),
                    "related_contact": None,
                }
            ),
            id="telegram_without_contact",
        ),
        pytest.param(
            lfc(
                lambda parametrized_telegram_delivery_method, personal_telegram_user_contact: {
                    "delivery_method": repackage_json(
                        TelegramDeliveryMethod.ResponseSchema,
                        parametrized_telegram_delivery_method,
                    ),
                    "related_contact": repackage_json(
                        UserContact.ResponseSchema,
                        personal_telegram_user_contact,
                    ),
                }
            ),
            id="telegram_with_contact",
        ),
    ],
)
async def test_retrieving_all_delivery_methods(
    authorized_client: TestClient,
    expected_email_delivery_method_data: TypeChecker,
    expected_telegram_delivery_method_data: TypeChecker,
) -> None:
    assert_response(
        authorized_client.get(
            "/api/protected/notification-service/users/current/delivery-methods/"
        ),
        expected_json={
            "email": expected_email_delivery_method_data,
            "telegram": expected_telegram_delivery_method_data,
        },
    )


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


# TODO parametrize for all kinds
@pytest.mark.usefixtures("parametrized_telegram_delivery_method")
async def test_delivery_method_removing(
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
            "/api/protected/notification-service/users/current"
            f"/delivery-methods/{DeliveryMethodKind.TELEGRAM}/"
        ),
    )

    remove_personal_telegram_contact_mock.assert_awaited_once_with(
        user_id=proxy_auth_data.user_id
    )

    async with active_session():
        assert (
            await TelegramDeliveryMethod.find_first_by_user_id(
                user_id=proxy_auth_data.user_id
            )
        ) is None


# TODO parametrize for all kinds
async def test_delivery_method_removing_delivery_method_not_found(
    authorized_client: TestClient,
) -> None:
    assert_response(
        authorized_client.delete(
            "/api/protected/notification-service/users/current"
            f"/delivery-methods/{DeliveryMethodKind.TELEGRAM}/"
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Delivery method not found"},
    )
