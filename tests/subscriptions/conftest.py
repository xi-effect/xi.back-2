from typing import Any

import pytest

from app.subscriptions.models.promocodes_db import Promocode
from tests.common.active_session import ActiveSession
from tests.common.types import AnyJSON, Factory
from tests.subscriptions import factories


@pytest.fixture(scope="session")
async def promocode_factory(active_session: ActiveSession) -> Factory[Promocode]:
    async def session_factory_inner(**kwargs: Any) -> Promocode:
        async with active_session():
            return await Promocode.create(**kwargs)

    return session_factory_inner


@pytest.fixture()
async def promocode_data() -> AnyJSON:
    return factories.LimitedPromocodeInputFactory.build_json()


@pytest.fixture()
async def promocode(
    promocode_factory: Factory[Promocode],
    promocode_data: AnyJSON,
) -> Promocode:
    return await promocode_factory(**promocode_data)


@pytest.fixture()
async def other_promocode_data() -> AnyJSON:
    return factories.LimitedPromocodeInputFactory.build_json()


@pytest.fixture()
async def other_promocode(
    promocode_factory: Factory[Promocode],
    other_promocode_data: AnyJSON,
) -> Promocode:
    return await promocode_factory(**other_promocode_data)


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
