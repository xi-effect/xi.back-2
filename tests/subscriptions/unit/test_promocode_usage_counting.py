import pytest

from app.subscriptions.models.promocodes_db import Promocode
from tests.common.active_session import ActiveSession
from tests.subscriptions import factories

pytestmark = pytest.mark.anyio


@pytest.mark.parametrize(
    ("usage_limit", "usage_count", "expected_result", "expected_usage_count"),
    [
        pytest.param(None, 0, True, 1, id="unlimited"),
        pytest.param(2, 1, True, 2, id="under_limit"),
        pytest.param(1, 1, False, 1, id="at_limit"),
    ],
)
async def test_usage_count_incrementing(
    active_session: ActiveSession,
    usage_limit: int | None,
    usage_count: int,
    expected_result: bool,
    expected_usage_count: int,
) -> None:
    async with active_session():
        promocode = await Promocode.create(
            **{
                **factories.UnrestrictedPromocodeInputFactory.build_python(
                    usage_limit=usage_limit,
                ),
                "usage_count": usage_count,
            },
        )

    async with active_session():
        result = await Promocode.has_incremented_usage_count_by_id(
            promocode_id=promocode.id
        )
        assert result == expected_result

    async with active_session():
        updated_promocode = await Promocode.find_first_by_id(promocode.id)
        assert updated_promocode is not None
        assert updated_promocode.usage_count == expected_usage_count
        await updated_promocode.delete()
