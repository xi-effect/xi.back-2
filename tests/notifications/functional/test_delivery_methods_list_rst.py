import random

import pytest
from pydantic_marshals.contains import TypeChecker, UnorderedLiteralCollection
from pytest_lazy_fixtures import lf
from starlette.testclient import TestClient

from app.common.schemas.notifications_sch import DeliveryMethodKind
from app.notifications.models.delivery_methods_db import (
    DeliveryMethod,
    EmailDeliveryMethod,
    TelegramDeliveryMethod,
    VKDeliveryMethod,
)
from app.notifications.models.disabled_delivery_routes_db import (
    DisabledDeliveryRoute,
    NotificationCategory,
)
from app.notifications.models.user_contacts_db import UserContact
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_response
from tests.common.utils import repackage_json

pytestmark = pytest.mark.anyio


def build_expected_delivery_method_data(
    delivery_method: DeliveryMethod,
    related_contact: UserContact | None = None,
    disabled_notification_categories: list[NotificationCategory] | None = None,
) -> TypeChecker:
    return {
        "delivery_method": repackage_json(
            DeliveryMethod.ResponseSchema,
            delivery_method,
        ),
        "related_contact": (
            None
            if related_contact is None
            else repackage_json(UserContact.ResponseSchema, related_contact)
        ),
        "enabled_notification_categories": UnorderedLiteralCollection(
            set(NotificationCategory).difference(disabled_notification_categories or [])
        ),
    }


def build_expected_delivery_methods_json(
    delivery_method: DeliveryMethod,
    expected_delivery_method_data: TypeChecker,
) -> TypeChecker:
    return {
        **dict.fromkeys(DeliveryMethodKind),
        delivery_method.kind: expected_delivery_method_data,
    }


@pytest.fixture()
async def expected_email_delivery_method_data_without_contact(
    active_email_delivery_method: EmailDeliveryMethod,
) -> TypeChecker:
    return build_expected_delivery_method_data(active_email_delivery_method)


@pytest.fixture()
async def expected_telegram_delivery_method_data_without_contact(
    active_telegram_delivery_method: TelegramDeliveryMethod,
) -> TypeChecker:
    return build_expected_delivery_method_data(active_telegram_delivery_method)


@pytest.fixture()
async def expected_telegram_delivery_method_data_with_contact(
    active_telegram_delivery_method: TelegramDeliveryMethod,
    personal_telegram_user_contact: UserContact,
) -> TypeChecker:
    return build_expected_delivery_method_data(
        active_telegram_delivery_method,
        related_contact=personal_telegram_user_contact,
    )


@pytest.fixture()
async def expected_vk_delivery_method_data_without_contact(
    active_vk_delivery_method: VKDeliveryMethod,
) -> TypeChecker:
    return build_expected_delivery_method_data(active_vk_delivery_method)


@pytest.fixture()
async def expected_vk_delivery_method_data_with_contact(
    active_vk_delivery_method: VKDeliveryMethod,
    personal_vk_user_contact: UserContact,
) -> TypeChecker:
    return build_expected_delivery_method_data(
        active_vk_delivery_method,
        related_contact=personal_vk_user_contact,
    )


@pytest.mark.parametrize(
    "expected_email_delivery_method_data",
    [
        pytest.param(None, id="no_email"),
        pytest.param(
            lf("expected_email_delivery_method_data_without_contact"),
            id="with_email",
        ),
    ],
)
@pytest.mark.parametrize(
    "expected_telegram_delivery_method_data",
    [
        pytest.param(None, id="no_telegram"),
        pytest.param(
            lf("expected_telegram_delivery_method_data_without_contact"),
            id="telegram_without_contact",
        ),
        pytest.param(
            lf("expected_telegram_delivery_method_data_with_contact"),
            id="telegram_with_contact",
        ),
    ],
)
@pytest.mark.parametrize(
    "expected_vk_delivery_method_data",
    [
        pytest.param(None, id="no_vk"),
        pytest.param(
            lf("expected_vk_delivery_method_data_without_contact"),
            id="vk_without_contact",
        ),
        pytest.param(
            lf("expected_vk_delivery_method_data_with_contact"),
            id="vk_with_contact",
        ),
    ],
)
async def test_retrieving_all_delivery_methods(
    authorized_client: TestClient,
    expected_email_delivery_method_data: TypeChecker,
    expected_telegram_delivery_method_data: TypeChecker,
    expected_vk_delivery_method_data: TypeChecker,
) -> None:
    assert_response(
        authorized_client.get(
            "/api/protected/notification-service/users/current/delivery-methods/"
        ),
        expected_json={
            "email": expected_email_delivery_method_data,
            "telegram": expected_telegram_delivery_method_data,
            "vk": expected_vk_delivery_method_data,
        },
    )


@pytest.mark.parametrize(
    "delivery_method",
    [
        pytest.param(lf("parametrized_email_delivery_method"), id="email"),
        pytest.param(lf("parametrized_telegram_delivery_method"), id="telegram"),
        pytest.param(lf("parametrized_vk_delivery_method"), id="vk"),
    ],
)
async def test_retrieving_all_delivery_methods_with_delivery_method_statuses(
    authorized_client: TestClient,
    delivery_method: DeliveryMethod,
) -> None:
    assert_response(
        authorized_client.get(
            "/api/protected/notification-service/users/current/delivery-methods/"
        ),
        expected_json=build_expected_delivery_methods_json(
            delivery_method,
            build_expected_delivery_method_data(delivery_method),
        ),
    )


@pytest.mark.parametrize(
    "disabled_delivery_route_count",
    [
        pytest.param(0, id="no_disabled_routes"),
        pytest.param(1, id="one_disabled_route"),
        pytest.param(2, id="two_disabled_routes"),
        pytest.param(len(NotificationCategory), id="all_disabled_routes"),
    ],
)
@pytest.mark.parametrize(
    "delivery_method",
    [
        pytest.param(lf("active_email_delivery_method"), id="email"),
        pytest.param(lf("active_telegram_delivery_method"), id="telegram"),
        pytest.param(lf("active_vk_delivery_method"), id="vk"),
    ],
)
async def test_retrieving_all_delivery_methods_with_disabled_delivery_routes(
    active_session: ActiveSession,
    authorized_client: TestClient,
    authorized_user_id: int,
    delivery_method: DeliveryMethod,
    disabled_delivery_route_count: int,
) -> None:
    disabled_notification_categories: list[NotificationCategory] = random.sample(
        list(NotificationCategory), k=disabled_delivery_route_count
    )

    async with active_session():
        for notification_category in disabled_notification_categories:
            await DisabledDeliveryRoute.create(
                user_id=authorized_user_id,
                delivery_method_kind=delivery_method.kind,
                notification_category=notification_category,
            )

    assert_response(
        authorized_client.get(
            "/api/protected/notification-service/users/current/delivery-methods/"
        ),
        expected_json=build_expected_delivery_methods_json(
            delivery_method,
            build_expected_delivery_method_data(
                delivery_method,
                disabled_notification_categories=disabled_notification_categories,
            ),
        ),
    )

    async with active_session():
        await DisabledDeliveryRoute.delete_by_kwargs(
            user_id=authorized_user_id,
            delivery_method_kind=delivery_method.kind,
        )
