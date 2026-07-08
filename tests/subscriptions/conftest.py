import pytest

from app.subscriptions.models.promocodes_db import Promocode
from tests.common.active_session import ActiveSession
from tests.common.types import AnyJSON
from tests.subscriptions import factories


@pytest.fixture()
async def promocode(active_session: ActiveSession) -> Promocode:
    async with active_session():
        return await Promocode.create(
            **{
                **factories.PromocodeNoCodeInputFactory.build_python(),
                **factories.LimitedPromocodeValidityPeriodInputFactory.build_python(),
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
                **factories.PromocodeNoCodeInputFactory.build_python(),
                **factories.LimitedPromocodeValidityPeriodInputFactory.build_python(),
            }
        )


@pytest.fixture()
async def deleted_promocode(
    active_session: ActiveSession, promocode: Promocode
) -> Promocode:
    async with active_session():
        await promocode.delete()
    return promocode
