import pytest
from pydantic_marshals.contains import assert_contains
from starlette import status
from starlette.testclient import TestClient

from app.common.schemas.notifications_sch import DeliveryMethodKind
from app.notifications.models.delivery_methods_db import (
    EmailDeliveryMethod,
)
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response
from tests.notifications import factories

pytestmark = pytest.mark.anyio


async def test_email_delivery_method_creation(
    active_session: ActiveSession,
    internal_client: TestClient,
    authorized_user_id: int,
) -> None:
    input_data = factories.EmailDeliveryMethodInputFactory.build_json()

    assert_nodata_response(
        internal_client.put(
            "/internal/notification-service"
            f"/users/{authorized_user_id}"
            f"/delivery-methods/{DeliveryMethodKind.EMAIL}/",
            json=input_data,
        ),
        expected_code=status.HTTP_201_CREATED,
    )

    async with active_session():
        delivery_method = await EmailDeliveryMethod.find_first_by_user_id(
            user_id=authorized_user_id
        )
        assert delivery_method is not None
        assert_contains(delivery_method, input_data)
        await delivery_method.delete()


async def test_email_delivery_method_updating(
    active_session: ActiveSession,
    internal_client: TestClient,
    active_email_delivery_method: EmailDeliveryMethod,
) -> None:
    input_data = factories.EmailDeliveryMethodInputFactory.build_json()

    assert_nodata_response(
        internal_client.put(
            "/internal/notification-service"
            f"/users/{active_email_delivery_method.user_id}"
            f"/delivery-methods/{DeliveryMethodKind.EMAIL}/",
            json=input_data,
        ),
    )

    async with active_session() as session:
        session.add(active_email_delivery_method)
        await session.refresh(active_email_delivery_method)
        assert_contains(active_email_delivery_method, input_data)
