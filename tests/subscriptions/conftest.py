from collections.abc import AsyncIterator

import pytest
from pytest_lazy_fixtures import lf

from app.subscriptions.models.promocodes_db import Promocode
from app.subscriptions.models.subscriptions_db import Subscription
from app.subscriptions.services.plans_svc import FREE_PLAN, PRO_PLAN
from tests.common.active_session import ActiveSession
from tests.common.types import AnyJSON, PytestRequest
from tests.subscriptions import factories


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
