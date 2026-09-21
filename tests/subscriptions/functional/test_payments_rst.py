from uuid import UUID

import pytest
from freezegun import freeze_time
from pydantic_marshals.contains import assert_contains
from starlette import status
from starlette.testclient import TestClient

from app.common.utils.datetime import datetime_utc_now
from app.subscriptions.models.payments_db import Payment
from app.subscriptions.routes.payments_rst import SubscriptionPeriod
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_response

pytestmark = pytest.mark.anyio


@pytest.mark.parametrize(
    ("period", "amount_roubles", "subscription_days"),
    [
        pytest.param(
            SubscriptionPeriod.MONTHLY, 1499, 30, id=SubscriptionPeriod.MONTHLY.value
        ),
        pytest.param(
            SubscriptionPeriod.YEARLY, 14999, 365, id=SubscriptionPeriod.YEARLY.value
        ),
    ],
)
@freeze_time()
async def test_payment_creation(
    active_session: ActiveSession,
    authorized_user_id: int,
    authorized_client: TestClient,
    period: SubscriptionPeriod,
    amount_roubles: int,
    subscription_days: int,
) -> None:
    payment_id: UUID = assert_response(
        authorized_client.post(
            "/api/protected/subscription-service/users/current/payments/",
            json={"period": period},
        ),
        expected_code=status.HTTP_201_CREATED,
        expected_json={
            "id": UUID,
            "provider_payment_id": str,
            "created_at": datetime_utc_now(),
            "amount_roubles": amount_roubles,
            "subscription_days": subscription_days,
            "completed_at": None,
            "cancellation_reason": None,
        },
    ).json()["id"]

    async with active_session():
        payment = await Payment.find_first_by_id(payment_id)
        assert payment is not None
        assert_contains(
            payment,
            {
                "user_id": authorized_user_id,
                "provider_payment_id": str(payment_id),
            },
        )
        await payment.delete()
