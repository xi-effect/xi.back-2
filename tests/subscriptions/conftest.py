import pytest

from app.subscriptions.models.promocodes_db import Promocode
from app.subscriptions.models.subscriptions_db import Subscription
from tests.common.active_session import ActiveSession
from tests.common.types import AnyJSON
from tests.subscriptions import factories


@pytest.fixture()
async def subscription(
    active_session: ActiveSession, authorized_user_id: int
) -> Subscription:
    async with active_session():
        return await Subscription.create(
            user_id=authorized_user_id,
            **factories.SubscriptionInputFactory.build_python(),
        )


@pytest.fixture()
async def subscription_data(subscription: Subscription) -> AnyJSON:
    return Subscription.ResponseSchema.model_validate(subscription).model_dump(
        mode="json"
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
