import pytest
from starlette.testclient import TestClient

from app.common.schemas.notifications_sch import DeliveryMethodKind
from app.notifications.models.disabled_delivery_routes_db import (
    DisabledDeliveryRoute,
    NotificationCategory,
)
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response
from tests.common.types import PytestRequest

pytestmark = pytest.mark.anyio


@pytest.fixture(
    params=[
        pytest.param(False, id="enabled_delivery_route"),
        pytest.param(True, id="disabled_delivery_route"),
    ]
)
async def existing_disabled_delivery_route(
    active_session: ActiveSession,
    authorized_user_id: int,
    random_delivery_method_kind: DeliveryMethodKind,
    random_notification_category: NotificationCategory,
    request: PytestRequest[bool],
) -> DisabledDeliveryRoute | None:
    if request.param:
        async with active_session():
            return await DisabledDeliveryRoute.create(
                user_id=authorized_user_id,
                delivery_method_kind=random_delivery_method_kind,
                notification_category=random_notification_category,
            )
    return None


@pytest.mark.usefixtures("existing_disabled_delivery_route")
async def test_delivery_route_enabling(
    active_session: ActiveSession,
    authorized_client: TestClient,
    authorized_user_id: int,
    random_delivery_method_kind: DeliveryMethodKind,
    random_notification_category: NotificationCategory,
) -> None:
    assert_nodata_response(
        authorized_client.put(
            "/api/protected/notification-service/users/current"
            f"/delivery-methods/{random_delivery_method_kind}"
            f"/enabled-notification-categories/{random_notification_category}/",
        ),
    )

    async with active_session():
        disabled_delivery_route = await DisabledDeliveryRoute.find_first_by_kwargs(
            user_id=authorized_user_id,
            delivery_method_kind=random_delivery_method_kind,
            notification_category=random_notification_category,
        )
        assert disabled_delivery_route is None


@pytest.mark.usefixtures("existing_disabled_delivery_route")
async def test_delivery_route_disabling(
    active_session: ActiveSession,
    authorized_client: TestClient,
    authorized_user_id: int,
    random_delivery_method_kind: DeliveryMethodKind,
    random_notification_category: NotificationCategory,
) -> None:
    assert_nodata_response(
        authorized_client.delete(
            "/api/protected/notification-service/users/current"
            f"/delivery-methods/{random_delivery_method_kind}"
            f"/enabled-notification-categories/{random_notification_category}/",
        ),
    )

    async with active_session():
        disabled_delivery_route = await DisabledDeliveryRoute.find_first_by_kwargs(
            user_id=authorized_user_id,
            delivery_method_kind=random_delivery_method_kind,
            notification_category=random_notification_category,
        )
        assert disabled_delivery_route is not None
        await disabled_delivery_route.delete()
