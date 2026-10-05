from collections.abc import AsyncIterator
from uuid import UUID

import pytest
from faker import Faker
from pytest_lazy_fixtures import lf
from starlette.testclient import TestClient

from app.common.config import settings
from app.common.dependencies.authorization_dep import ProxyAuthData
from app.common.utils.datetime import datetime_utc_now
from app.subscriptions.models.auto_renewals_db import AutoRenewal
from app.subscriptions.models.payments_db import Payment
from app.subscriptions.models.promocodes_db import Promocode
from app.subscriptions.models.subscriptions_db import Subscription
from app.subscriptions.services.plans_svc import FREE_PLAN, PRO_PLAN
from tests.common.active_session import ActiveSession
from tests.common.types import AnyJSON, PytestRequest
from tests.factories import ProxyAuthDataFactory
from tests.subscriptions import factories


@pytest.fixture()
def outsider_auth_data() -> ProxyAuthData:
    return ProxyAuthDataFactory.build()


@pytest.fixture()
def outsider_client(
    client: TestClient, outsider_auth_data: ProxyAuthData
) -> TestClient:
    return TestClient(client.app, headers=outsider_auth_data.as_headers)


@pytest.fixture()
async def active_subscription(
    active_session: ActiveSession, authorized_user_id: int
) -> AsyncIterator[Subscription]:
    async with active_session():
        subscription = await Subscription.create(
            user_id=authorized_user_id,
            **factories.ActiveSubscriptionInputFactory.build_python(),
        )

    yield subscription

    async with active_session():
        await subscription.delete()


@pytest.fixture()
async def expired_subscription(
    active_session: ActiveSession, authorized_user_id: int
) -> AsyncIterator[Subscription]:
    async with active_session():
        subscription = await Subscription.create(
            user_id=authorized_user_id,
            **factories.ExpiredSubscriptionInputFactory.build_python(),
        )

    yield subscription

    async with active_session():
        await subscription.delete()


@pytest.fixture(
    params=[
        pytest.param(lf("active_subscription"), id="active_subscription"),
        pytest.param(lf("expired_subscription"), id="expired_subscription"),
    ],
)
def parametrized_subscription(request: PytestRequest[Subscription]) -> Subscription:
    return request.param


plan_parametrization = pytest.mark.parametrize(
    ("subscription", "expected_plan_data"),
    [
        pytest.param(None, FREE_PLAN, id="no_subscription"),
        pytest.param(
            lf("expired_subscription"),
            FREE_PLAN,
            id="expired_subscription",
        ),
        pytest.param(
            lf("active_subscription"),
            PRO_PLAN,
            id="active_subscription",
        ),
    ],
)


@pytest.fixture()
async def auto_renewal(
    active_session: ActiveSession, authorized_user_id: int
) -> AsyncIterator[AutoRenewal]:
    async with active_session():
        auto_renewal = await AutoRenewal.create(
            user_id=authorized_user_id,
            **factories.AutoRenewalInputFactory.build_python(),
        )

    yield auto_renewal

    async with active_session():
        await AutoRenewal.delete_by_kwargs(user_id=authorized_user_id)


@pytest.fixture()
async def promocode(active_session: ActiveSession) -> Promocode:
    async with active_session():
        return await Promocode.create(
            **{
                **factories.PromocodeWithCodeInputFactory.build_python(),
                **factories.LimitedPeriodPromocodeSettingsFactory.build_python(),
            }
        )


@pytest.fixture()
async def promocode_data(promocode: Promocode) -> AnyJSON:
    return Promocode.ResponseSchema.model_validate(promocode).model_dump(mode="json")


@pytest.fixture()
async def other_promocode(active_session: ActiveSession) -> Promocode:
    async with active_session():
        return await Promocode.create(
            **{
                **factories.PromocodeWithCodeInputFactory.build_python(),
                **factories.LimitedPeriodPromocodeSettingsFactory.build_python(),
            }
        )


@pytest.fixture()
async def deleted_promocode(
    active_session: ActiveSession, promocode: Promocode
) -> Promocode:
    async with active_session():
        await promocode.delete()
    return promocode


@pytest.fixture(scope="session")
def yookassa_credentials() -> str:
    return f"{settings.yookassa_shop_id}:{settings.yookassa_secret_key}"


@pytest.fixture()
async def pending_payment(
    active_session: ActiveSession, authorized_user_id: int
) -> AsyncIterator[Payment]:
    async with active_session():
        payment = await Payment.create(
            user_id=authorized_user_id,
            **factories.StoredPaymentInputFactory.build_python(),
        )

    yield payment

    async with active_session():
        await Payment.delete_by_kwargs(id=payment.id)


@pytest.fixture()
async def completed_payment(
    active_session: ActiveSession, authorized_user_id: int
) -> AsyncIterator[Payment]:
    async with active_session():
        payment = await Payment.create(
            user_id=authorized_user_id,
            completed_at=datetime_utc_now(),
            **factories.StoredPaymentInputFactory.build_python(),
        )

    yield payment

    async with active_session():
        await Payment.delete_by_kwargs(id=payment.id)


@pytest.fixture()
async def cancelled_payment(
    faker: Faker, active_session: ActiveSession, authorized_user_id: int
) -> AsyncIterator[Payment]:
    async with active_session():
        payment = await Payment.create(
            user_id=authorized_user_id,
            completed_at=datetime_utc_now(),
            cancellation_reason=faker.sentence(),
            **factories.StoredPaymentInputFactory.build_python(),
        )

    yield payment

    async with active_session():
        await Payment.delete_by_kwargs(id=payment.id)


@pytest.fixture(
    params=[
        pytest.param(lf("pending_payment"), id="pending_payment"),
        pytest.param(lf("completed_payment"), id="completed_payment"),
        pytest.param(lf("cancelled_payment"), id="cancelled_payment"),
    ],
)
def parametrized_payment(request: PytestRequest[Payment]) -> Payment:
    return request.param


@pytest.fixture()
async def deleted_payment_id(
    active_session: ActiveSession, pending_payment: Payment
) -> UUID:
    async with active_session():
        await pending_payment.delete()
    return pending_payment.id
