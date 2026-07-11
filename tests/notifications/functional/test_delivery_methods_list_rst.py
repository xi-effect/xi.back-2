import random
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import pytest
from pydantic_marshals.contains import TypeChecker, UnorderedLiteralCollection
from pytest_lazy_fixtures import lf
from starlette.testclient import TestClient

from app.common.schemas.notifications_sch import DeliveryMethodKind
from app.notifications.models.delivery_methods_db import (
    EmailDeliveryMethod,
    TelegramDeliveryMethod,
)
from app.notifications.models.disabled_delivery_routes_db import (
    DisabledDeliveryRoute,
    NotificationCategory,
)
from app.notifications.models.user_contacts_db import UserContact
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_response
from tests.common.types import PytestRequest
from tests.common.utils import repackage_json

pytestmark = pytest.mark.anyio


@asynccontextmanager
async def disabled_delivery_routes_context(
    active_session: ActiveSession,
    authorized_user_id: int,
    request: PytestRequest[int],
    delivery_method_kind: DeliveryMethodKind,
) -> AsyncIterator[list[DisabledDeliveryRoute]]:
    if request.param == 0:
        yield []
        return

    async with active_session():
        disabled_delivery_routes = [
            await DisabledDeliveryRoute.create(
                user_id=authorized_user_id,
                delivery_method_kind=delivery_method_kind,
                notification_category=notification_category,
            )
            for notification_category in random.sample(
                list(NotificationCategory), k=request.param
            )
        ]

    yield disabled_delivery_routes

    async with active_session():
        for disabled_delivery_route in disabled_delivery_routes:
            await disabled_delivery_route.delete()


@pytest.fixture(
    params=[
        pytest.param(0, id="no_disabled_email_routes"),
        pytest.param(1, id="one_disabled_email_route"),
        pytest.param(2, id="two_disabled_email_route"),
        pytest.param(len(NotificationCategory), id="all_disabled_email_routes"),
    ]
)
async def disabled_delivery_routes_for_email(
    active_session: ActiveSession,
    authorized_user_id: int,
    request: PytestRequest[int],
) -> AsyncIterator[list[DisabledDeliveryRoute]]:
    async with disabled_delivery_routes_context(
        active_session=active_session,
        authorized_user_id=authorized_user_id,
        request=request,
        delivery_method_kind=DeliveryMethodKind.EMAIL,
    ) as disabled_delivery_routes:
        yield disabled_delivery_routes


@pytest.fixture(
    params=[
        pytest.param(0, id="no_disabled_telegram_routes"),
        pytest.param(1, id="one_disabled_telegram_route"),
        pytest.param(2, id="two_disabled_telegram_route"),
        pytest.param(len(NotificationCategory), id="all_disabled_telegram_routes"),
    ]
)
async def disabled_delivery_routes_for_telegram(
    active_session: ActiveSession,
    authorized_user_id: int,
    request: PytestRequest[int],
) -> AsyncIterator[list[DisabledDeliveryRoute]]:
    async with disabled_delivery_routes_context(
        active_session=active_session,
        authorized_user_id=authorized_user_id,
        request=request,
        delivery_method_kind=DeliveryMethodKind.TELEGRAM,
    ) as disabled_delivery_routes:
        yield disabled_delivery_routes


@pytest.fixture()
async def expected_email_delivery_method_data_without_contact(
    parametrized_email_delivery_method: EmailDeliveryMethod,
    disabled_delivery_routes_for_email: list[DisabledDeliveryRoute],
) -> TypeChecker:
    return {
        "delivery_method": repackage_json(
            EmailDeliveryMethod.ResponseSchema,
            parametrized_email_delivery_method,
        ),
        "related_contact": None,
        "enabled_notification_categories": UnorderedLiteralCollection(
            set(NotificationCategory).difference(
                disabled_delivery_route.notification_category
                for disabled_delivery_route in disabled_delivery_routes_for_email
            )
        ),
    }


@pytest.fixture()
async def expected_telegram_delivery_method_data_without_contact(
    parametrized_telegram_delivery_method: TelegramDeliveryMethod,
    disabled_delivery_routes_for_telegram: list[DisabledDeliveryRoute],
) -> TypeChecker:
    return {
        "delivery_method": repackage_json(
            TelegramDeliveryMethod.ResponseSchema,
            parametrized_telegram_delivery_method,
        ),
        "related_contact": None,
        "enabled_notification_categories": UnorderedLiteralCollection(
            set(NotificationCategory).difference(
                disabled_delivery_route.notification_category
                for disabled_delivery_route in disabled_delivery_routes_for_telegram
            )
        ),
    }


@pytest.fixture()
async def expected_telegram_delivery_method_data_with_contact(
    parametrized_telegram_delivery_method: TelegramDeliveryMethod,
    personal_telegram_user_contact: UserContact,
    disabled_delivery_routes_for_telegram: list[DisabledDeliveryRoute],
) -> TypeChecker:
    return {
        "delivery_method": repackage_json(
            TelegramDeliveryMethod.ResponseSchema,
            parametrized_telegram_delivery_method,
        ),
        "related_contact": repackage_json(
            UserContact.ResponseSchema,
            personal_telegram_user_contact,
        ),
        "enabled_notification_categories": UnorderedLiteralCollection(
            set(NotificationCategory).difference(
                disabled_delivery_route.notification_category
                for disabled_delivery_route in disabled_delivery_routes_for_telegram
            )
        ),
    }


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
