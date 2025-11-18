import pytest

from app.subscriptions.models.promocodes_db import Promocode
from tests.common.active_session import ActiveSession
from tests.common.types import AnyJSON
from tests.subscriptions import factories


@pytest.fixture()
async def promocode(active_session: ActiveSession) -> Promocode:
    async with active_session():
        return await Promocode.create(**factories.PromocodeInputFactory.build_python())


@pytest.fixture()
async def promocode_data(promocode: Promocode) -> AnyJSON:
    return Promocode.ResponseSchema.model_validate(
        promocode, from_attributes=True
    ).model_dump(mode="json")


@pytest.fixture()
def promocode_id(promocode: Promocode) -> int:
    return promocode.id


@pytest.fixture()
async def deleted_promocode_id(
    active_session: ActiveSession, promocode: Promocode
) -> int:
    async with active_session():
        await promocode.delete()
    return promocode.id


@pytest.fixture()
async def deleted_promocode_code(
    active_session: ActiveSession, promocode: Promocode
) -> str:
    async with active_session():
        await promocode.delete()
    return promocode.code
