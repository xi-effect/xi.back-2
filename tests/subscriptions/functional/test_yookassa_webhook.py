from base64 import b64encode
from datetime import datetime, timedelta
from typing import Any

import pytest
from faker import Faker
from freezegun import freeze_time
from pydantic_marshals.contains import assert_contains
from pytest_lazy_fixtures import lf
from respx import MockRouter, Route
from starlette import status
from starlette.testclient import TestClient

from app.common.schemas.subscriptions_sch import PaidPlanKind
from app.common.utils.datetime import datetime_utc_now
from app.subscriptions.models.auto_renewals_db import AutoRenewal
from app.subscriptions.models.payments_db import Payment
from app.subscriptions.models.subscriptions_db import Subscription
from app.subscriptions.routes.yookassa_webhook_rst import (
    InvalidPaymentStatusException,
    SucceededPaymentNotFoundException,
    UnexpectedYooKassaEventException,
)
from app.subscriptions.schemas.payments_sch import PaymentCorrelationSchema
from app.subscriptions.schemas.subscriptions_sch import SubscriptionPeriod
from app.subscriptions.schemas.yookassa_sch import (
    YooKassaCanceledPaymentSchema,
    YooKassaEventSchema,
    YooKassaEventType,
    YooKassaPaymentMethodSchema,
)
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response
from tests.common.polyfactory_ext import BaseModelFactory
from tests.common.respx_ext import assert_last_httpx_request
from tests.subscriptions import factories

pytestmark = pytest.mark.anyio


@pytest.fixture()
def yookassa_retrieve_payment_mock(
    yookassa_respx_mock: MockRouter, pending_payment: Payment
) -> Route:
    return yookassa_respx_mock.get(
        path=f"/payments/{pending_payment.provider_payment_id}"
    )


@pytest.mark.parametrize(
    ("existing_subscription", "subscription_extended_from"),
    [
        pytest.param(None, None, id="no_subscription"),
        pytest.param(lf("expired_subscription"), None, id="expired_subscription"),
        pytest.param(
            lf("active_subscription"),
            lf("active_subscription.ends_at"),
            id="active_subscription",
        ),
    ],
)
@freeze_time()
async def test_handling_event_from_yookassa_payment_succeeded(
    active_session: ActiveSession,
    client: TestClient,
    authorized_user_id: int,
    yookassa_credentials: str,
    pending_payment: Payment,
    yookassa_retrieve_payment_mock: Route,
    existing_subscription: Subscription | None,
    subscription_extended_from: datetime | None,
) -> None:
    yookassa_retrieve_payment_mock.respond(
        json=factories.YooKassaSucceededPaymentFactory.build_json(
            metadata=PaymentCorrelationSchema(payment_id=pending_payment.id)
        )
    )

    assert_nodata_response(
        client.post(
            "/api/public/subscription-service/yookassa-events/",
            json=factories.YooKassaEventFactory.build_json(
                event=YooKassaEventType.PAYMENT_SUCCEEDED,
                object=factories.YooKassaEventObjectFactory.build(
                    id=pending_payment.provider_payment_id
                ),
            ),
        ),
        expected_code=status.HTTP_200_OK,
    )

    async with active_session() as session:
        session.add(pending_payment)
        await session.refresh(pending_payment)
        assert_contains(
            pending_payment,
            {"completed_at": datetime_utc_now(), "cancellation_reason": None},
        )

        subscription = await Subscription.find_first_by_id(authorized_user_id)
        assert subscription is not None
        assert_contains(
            subscription,
            {
                "plan_kind": PaidPlanKind.PRO,
                "ends_at": (subscription_extended_from or datetime_utc_now())
                + timedelta(days=pending_payment.subscription_days),
            },
        )
        if existing_subscription is None:
            await subscription.delete()

    assert_last_httpx_request(
        yookassa_retrieve_payment_mock,
        expected_headers={
            "Authorization": f"Basic {b64encode(yookassa_credentials.encode()).decode()}",
        },
    )


@pytest.mark.parametrize(
    "existing_auto_renewal",
    [
        pytest.param(None, id="no_auto_renewal"),
        pytest.param(lf("auto_renewal"), id="existing_auto_renewal"),
    ],
)
async def test_handling_event_from_yookassa_payment_succeeded_recording_auto_renewal(
    active_session: ActiveSession,
    client: TestClient,
    authorized_user_id: int,
    random_subscription_period: SubscriptionPeriod,
    yookassa_credentials: str,
    pending_payment: Payment,
    yookassa_retrieve_payment_mock: Route,
    existing_auto_renewal: AutoRenewal | None,
) -> None:
    payment_method: YooKassaPaymentMethodSchema = (
        factories.YooKassaPaymentMethodFactory.build(saved=True)
    )
    yookassa_retrieve_payment_mock.respond(
        json=factories.YooKassaSucceededPaymentFactory.build_json(
            metadata=PaymentCorrelationSchema(
                payment_id=pending_payment.id,
                auto_renewal_period=random_subscription_period,
            ),
            payment_method=payment_method,
        )
    )

    assert_nodata_response(
        client.post(
            "/api/public/subscription-service/yookassa-events/",
            json=factories.YooKassaEventFactory.build_json(
                event=YooKassaEventType.PAYMENT_SUCCEEDED,
                object=factories.YooKassaEventObjectFactory.build(
                    id=pending_payment.provider_payment_id
                ),
            ),
        ),
        expected_code=status.HTTP_200_OK,
    )

    async with active_session():
        subscription = await Subscription.find_first_by_id(authorized_user_id)
        assert subscription is not None
        await subscription.delete()

        auto_renewal = await AutoRenewal.find_first_by_id(authorized_user_id)
        assert auto_renewal is not None
        assert_contains(
            auto_renewal,
            {
                "provider_payment_method_id": payment_method.id,
                "renewal_period": random_subscription_period,
            },
        )
        if existing_auto_renewal is None:
            await auto_renewal.delete()

    assert_last_httpx_request(
        yookassa_retrieve_payment_mock,
        expected_headers={
            "Authorization": f"Basic {b64encode(yookassa_credentials.encode()).decode()}",
        },
    )


@pytest.mark.parametrize(
    ("has_auto_renewal_period", "is_payment_method_saved"),
    [
        pytest.param(False, True, id="no_auto_renewal_period"),
        pytest.param(True, False, id="unsaved_payment_method"),
    ],
)
async def test_handling_event_from_yookassa_payment_succeeded_clearing_auto_renewal(
    active_session: ActiveSession,
    client: TestClient,
    authorized_user_id: int,
    random_subscription_period: SubscriptionPeriod,
    auto_renewal: AutoRenewal,
    yookassa_credentials: str,
    pending_payment: Payment,
    yookassa_retrieve_payment_mock: Route,
    has_auto_renewal_period: bool,
    is_payment_method_saved: bool,
) -> None:
    yookassa_retrieve_payment_mock.respond(
        json=factories.YooKassaSucceededPaymentFactory.build_json(
            metadata=PaymentCorrelationSchema(
                payment_id=pending_payment.id,
                auto_renewal_period=(
                    random_subscription_period if has_auto_renewal_period else None
                ),
            ),
            payment_method=factories.YooKassaPaymentMethodFactory.build(
                saved=is_payment_method_saved
            ),
        )
    )

    assert_nodata_response(
        client.post(
            "/api/public/subscription-service/yookassa-events/",
            json=factories.YooKassaEventFactory.build_json(
                event=YooKassaEventType.PAYMENT_SUCCEEDED,
                object=factories.YooKassaEventObjectFactory.build(
                    id=pending_payment.provider_payment_id
                ),
            ),
        ),
        expected_code=status.HTTP_200_OK,
    )

    async with active_session():
        subscription = await Subscription.find_first_by_id(authorized_user_id)
        assert subscription is not None
        await subscription.delete()

        assert await AutoRenewal.find_first_by_id(authorized_user_id) is None

    assert_last_httpx_request(
        yookassa_retrieve_payment_mock,
        expected_headers={
            "Authorization": f"Basic {b64encode(yookassa_credentials.encode()).decode()}",
        },
    )


async def test_handling_event_from_yookassa_payment_succeeded_payment_not_found(
    yookassa_respx_mock: MockRouter,
    client: TestClient,
    yookassa_credentials: str,
) -> None:
    yookassa_event: YooKassaEventSchema = factories.YooKassaEventFactory.build(
        event=YooKassaEventType.PAYMENT_SUCCEEDED
    )
    yookassa_retrieve_payment_mock = yookassa_respx_mock.get(
        path=f"/payments/{yookassa_event.object.id}"
    ).respond(json=factories.YooKassaSucceededPaymentFactory.build_json())

    with pytest.raises(SucceededPaymentNotFoundException):
        client.post(
            "/api/public/subscription-service/yookassa-events/",
            json=yookassa_event.model_dump(mode="json"),
        )

    assert_last_httpx_request(
        yookassa_retrieve_payment_mock,
        expected_headers={
            "Authorization": f"Basic {b64encode(yookassa_credentials.encode()).decode()}",
        },
    )


@freeze_time()
async def test_handling_event_from_yookassa_payment_canceled(
    active_session: ActiveSession,
    client: TestClient,
    authorized_user_id: int,
    yookassa_credentials: str,
    pending_payment: Payment,
    yookassa_retrieve_payment_mock: Route,
) -> None:
    yookassa_payment: YooKassaCanceledPaymentSchema = (
        factories.YooKassaCanceledPaymentFactory.build(
            metadata=PaymentCorrelationSchema(payment_id=pending_payment.id)
        )
    )
    yookassa_retrieve_payment_mock.respond(
        json=yookassa_payment.model_dump(mode="json")
    )

    assert_nodata_response(
        client.post(
            "/api/public/subscription-service/yookassa-events/",
            json=factories.YooKassaEventFactory.build_json(
                event=YooKassaEventType.PAYMENT_CANCELED,
                object=factories.YooKassaEventObjectFactory.build(
                    id=pending_payment.provider_payment_id
                ),
            ),
        ),
        expected_code=status.HTTP_200_OK,
    )

    async with active_session() as session:
        session.add(pending_payment)
        await session.refresh(pending_payment)
        assert_contains(
            pending_payment,
            {
                "completed_at": datetime_utc_now(),
                "cancellation_reason": yookassa_payment.cancellation_details.reason,
            },
        )

        assert await Subscription.find_first_by_id(authorized_user_id) is None

    assert_last_httpx_request(
        yookassa_retrieve_payment_mock,
        expected_headers={
            "Authorization": f"Basic {b64encode(yookassa_credentials.encode()).decode()}",
        },
    )


async def test_handling_event_from_yookassa_payment_canceled_payment_not_found(
    yookassa_respx_mock: MockRouter,
    client: TestClient,
    yookassa_credentials: str,
) -> None:
    yookassa_event: YooKassaEventSchema = factories.YooKassaEventFactory.build(
        event=YooKassaEventType.PAYMENT_CANCELED
    )
    yookassa_retrieve_payment_mock = yookassa_respx_mock.get(
        path=f"/payments/{yookassa_event.object.id}"
    ).respond(json=factories.YooKassaCanceledPaymentFactory.build_json())

    assert_nodata_response(
        client.post(
            "/api/public/subscription-service/yookassa-events/",
            json=yookassa_event.model_dump(mode="json"),
        ),
        expected_code=status.HTTP_200_OK,
    )

    assert_last_httpx_request(
        yookassa_retrieve_payment_mock,
        expected_headers={
            "Authorization": f"Basic {b64encode(yookassa_credentials.encode()).decode()}",
        },
    )


@pytest.mark.parametrize(
    ("event_type", "yookassa_payment_factory"),
    [
        pytest.param(
            YooKassaEventType.PAYMENT_SUCCEEDED,
            factories.YooKassaSucceededPaymentFactory,
            id="payment_succeeded",
        ),
        pytest.param(
            YooKassaEventType.PAYMENT_CANCELED,
            factories.YooKassaCanceledPaymentFactory,
            id="payment_canceled",
        ),
    ],
)
async def test_handling_event_from_yookassa_payment_already_completed(
    active_session: ActiveSession,
    yookassa_respx_mock: MockRouter,
    client: TestClient,
    authorized_user_id: int,
    yookassa_credentials: str,
    completed_payment: Payment,
    event_type: YooKassaEventType,
    yookassa_payment_factory: type[BaseModelFactory[Any]],
) -> None:
    yookassa_retrieve_payment_mock = yookassa_respx_mock.get(
        path=f"/payments/{completed_payment.provider_payment_id}"
    ).respond(
        json=yookassa_payment_factory.build_json(
            metadata=PaymentCorrelationSchema(payment_id=completed_payment.id)
        )
    )

    assert_nodata_response(
        client.post(
            "/api/public/subscription-service/yookassa-events/",
            json=factories.YooKassaEventFactory.build_json(
                event=event_type,
                object=factories.YooKassaEventObjectFactory.build(
                    id=completed_payment.provider_payment_id
                ),
            ),
        ),
        expected_code=status.HTTP_200_OK,
    )

    async with active_session():
        payment = await Payment.find_first_by_id(completed_payment.id)
        assert payment is not None
        assert_contains(
            payment,
            {
                "completed_at": completed_payment.completed_at,
                "cancellation_reason": None,
            },
        )

        assert await Subscription.find_first_by_id(authorized_user_id) is None

    assert_last_httpx_request(
        yookassa_retrieve_payment_mock,
        expected_headers={
            "Authorization": f"Basic {b64encode(yookassa_credentials.encode()).decode()}",
        },
    )


async def test_handling_event_from_yookassa_unexpected_event(
    faker: Faker,
    yookassa_respx_mock: MockRouter,
    client: TestClient,
) -> None:
    with pytest.raises(UnexpectedYooKassaEventException):
        client.post(
            "/api/public/subscription-service/yookassa-events/",
            json=factories.YooKassaEventFactory.build_json(event=faker.pystr()),
        )

    assert yookassa_respx_mock.calls.call_count == 0


@pytest.mark.parametrize(
    "yookassa_payment_factory",
    [
        pytest.param(factories.YooKassaPendingPaymentFactory, id="pending"),
        pytest.param(
            factories.YooKassaWaitingForCapturePaymentFactory,
            id="waiting_for_capture",
        ),
    ],
)
async def test_handling_event_from_yookassa_invalid_payment_status(
    active_session: ActiveSession,
    client: TestClient,
    authorized_user_id: int,
    yookassa_credentials: str,
    pending_payment: Payment,
    yookassa_retrieve_payment_mock: Route,
    yookassa_payment_factory: type[BaseModelFactory[Any]],
) -> None:
    yookassa_retrieve_payment_mock.respond(
        json=yookassa_payment_factory.build_json(
            metadata=PaymentCorrelationSchema(payment_id=pending_payment.id)
        )
    )

    with pytest.raises(InvalidPaymentStatusException):
        client.post(
            "/api/public/subscription-service/yookassa-events/",
            json=factories.YooKassaEventFactory.build_json(
                event=YooKassaEventType.PAYMENT_SUCCEEDED,
                object=factories.YooKassaEventObjectFactory.build(
                    id=pending_payment.provider_payment_id
                ),
            ),
        )

    async with active_session() as session:
        session.add(pending_payment)
        await session.refresh(pending_payment)
        assert_contains(
            pending_payment,
            {"completed_at": None, "cancellation_reason": None},
        )

        assert await Subscription.find_first_by_id(authorized_user_id) is None

    assert_last_httpx_request(
        yookassa_retrieve_payment_mock,
        expected_headers={
            "Authorization": f"Basic {b64encode(yookassa_credentials.encode()).decode()}",
        },
    )
