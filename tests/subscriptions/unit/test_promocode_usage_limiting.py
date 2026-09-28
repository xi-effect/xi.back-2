import pytest
from pydantic_marshals.contains import assert_contains

from app.subscriptions.models.promocodes_db import Promocode
from tests.common.active_session import ActiveSession
from tests.common.polyfactory_ext import BaseModelFactory
from tests.subscriptions import factories

pytestmark = pytest.mark.anyio


@pytest.mark.parametrize(
    ("usage_state_factory", "expected_incremented"),
    [
        pytest.param(
            factories.UnlimitedPromocodeUsageStateFactory, True, id="unlimited"
        ),
        pytest.param(
            factories.UnderLimitPromocodeUsageStateFactory, True, id="under_limit"
        ),
        pytest.param(factories.AtLimitPromocodeUsageStateFactory, False, id="at_limit"),
    ],
)
async def test_promocode_usage_limiting(
    active_session: ActiveSession,
    usage_state_factory: type[BaseModelFactory[factories.PromocodeUsageStateSchema]],
    expected_incremented: bool,
) -> None:
    usage_state = usage_state_factory.build()
    expected_usage_count = usage_state.usage_count
    if expected_incremented:
        expected_usage_count += 1

    async with active_session():
        promocode = await Promocode.create(
            **{
                **factories.UnrestrictedPromocodeInputFactory.build_python(),
                **usage_state.model_dump(),
            },
        )

    async with active_session():
        result = await Promocode.find_and_increment_usage_count_by_id(
            promocode_id=promocode.id,
        )

    assert expected_incremented is (result is not None)

    async with active_session():
        updated_promocode = await Promocode.find_first_by_id(promocode.id)
        assert updated_promocode is not None
        assert_contains(updated_promocode, {"usage_count": expected_usage_count})
        await updated_promocode.delete()


async def test_promocode_usage_limiting_not_found(
    active_session: ActiveSession,
    deleted_promocode: Promocode,
) -> None:
    async with active_session():
        result = await Promocode.find_and_increment_usage_count_by_id(
            promocode_id=deleted_promocode.id,
        )

    assert result is None
