from base64 import b64encode
from uuid import UUID

import pytest
from freezegun import freeze_time
from pydantic_marshals.contains import assert_contains
from respx import MockRouter
from starlette import status
from starlette.testclient import TestClient

from app.common.config import settings
from app.common.schemas.users_sch import DetailedUserSchema
from app.common.utils.datetime import datetime_utc_now
from app.subscriptions.models.payments_db import Payment
from app.subscriptions.routes.payments_rst import (
    RECEIPT_ITEM_DESCRIPTION_TEMPLATE,
    SubscriptionPeriod,
)
from app.subscriptions.schemas.yookassa_sch import YooKassaPaymentResponseSchema
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_response
from tests.common.respx_ext import assert_last_httpx_request
from tests.factories import DetailedUserFactory
from tests.subscriptions import factories

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
    users_internal_respx_mock: MockRouter,
    yookassa_respx_mock: MockRouter,
    authorized_user_id: int,
    authorized_client: TestClient,
    period: SubscriptionPeriod,
    amount_roubles: int,
    subscription_days: int,
) -> None:
    user: DetailedUserSchema = DetailedUserFactory.build()
    users_internal_bridge_mock = users_internal_respx_mock.get(
        path=f"/users/{authorized_user_id}/"
    ).respond(json=user.model_dump(mode="json"))

    yookassa_payment: YooKassaPaymentResponseSchema = (
        factories.YooKassaPaymentResponseFactory.build()
    )
    yookassa_create_payment_mock = yookassa_respx_mock.post(path="/payments").respond(
        json=yookassa_payment.model_dump(mode="json")
    )

    payment_id: UUID = assert_response(
        authorized_client.post(
            "/api/protected/subscription-service/users/current/payments/",
            json={"period": period},
        ),
        expected_code=status.HTTP_201_CREATED,
        expected_json={
            "payment": {
                "id": UUID,
                "provider_payment_id": yookassa_payment.id,
                "created_at": datetime_utc_now(),
                "amount_roubles": amount_roubles,
                "subscription_days": subscription_days,
                "completed_at": None,
                "cancellation_reason": None,
            },
            "confirmation_url": yookassa_payment.confirmation.confirmation_url,
        },
    ).json()["payment"]["id"]

    async with active_session():
        payment = await Payment.find_first_by_id(payment_id)
        assert payment is not None
        assert_contains(payment, {"user_id": authorized_user_id})
        await payment.delete()

    assert_last_httpx_request(
        users_internal_bridge_mock,
        expected_headers={"X-Api-Key": settings.api_key},
    )

    yookassa_credentials: str = (
        f"{settings.yookassa_shop_id}:{settings.yookassa_secret_key}"
    )
    assert_last_httpx_request(
        yookassa_create_payment_mock,
        expected_headers={
            "Authorization": f"Basic {b64encode(yookassa_credentials.encode()).decode()}",
            "Idempotence-Key": str(payment_id),
        },
        expected_json={
            "amount": {"value": f"{amount_roubles:.2f}", "currency": "RUB"},
            "capture": True,
            "confirmation": {
                "type": "redirect",
                "return_url": settings.yookassa_return_url,
            },
            "receipt": {
                "customer": {"email": user.email},
                "items": [
                    {
                        "description": RECEIPT_ITEM_DESCRIPTION_TEMPLATE.format(
                            subscription_days=subscription_days
                        ),
                        "amount": {"value": f"{amount_roubles:.2f}", "currency": "RUB"},
                        "vat_code": 1,
                        "quantity": 1,
                        "measure": "piece",
                        "payment_subject": "service",
                        "payment_mode": "full_payment",
                    }
                ],
            },
            "metadata": {"payment_id": str(payment_id)},
        },
    )
