import pytest
from faker import Faker
from pydantic_marshals.contains import assert_contains

from app.subscriptions.models.promocodes_db import Promocode
from tests.common.active_session import ActiveSession
from tests.subscriptions import factories

pytestmark = pytest.mark.anyio


async def test_find_and_increment_usage_count_by_id_no_usage_limit(
    active_session: ActiveSession,
) -> None:
    async with active_session():
        promocode = await Promocode.create(
            **{
                **factories.PromocodeWithCodeInputFactory.build_python(),
                **factories.UnrestrictedPromocodeSettingsFactory.build_python(),
            }
        )

    async with active_session():
        assert_contains(
            await Promocode.find_and_increment_usage_count_by_id(
                promocode_id=promocode.id,
            ),
            {"usage_count": promocode.usage_count + 1},
        )

    async with active_session():
        await promocode.delete()


async def test_find_and_increment_usage_count_by_id_usage_limit_not_reached(
    faker: Faker,
    active_session: ActiveSession,
) -> None:
    usage_count: int = faker.pyint(min_value=0, max_value=100)

    async with active_session():
        promocode = await Promocode.create(
            **{
                **factories.PromocodeWithCodeInputFactory.build_python(),
                **factories.UnrestrictedPromocodeSettingsFactory.build_python(),
                "usage_count": usage_count,
                "usage_limit": faker.pyint(min_value=usage_count + 1, max_value=200),
            }
        )

    async with active_session():
        assert_contains(
            await Promocode.find_and_increment_usage_count_by_id(
                promocode_id=promocode.id,
            ),
            {"usage_count": usage_count + 1},
        )

    async with active_session():
        await promocode.delete()


async def test_find_and_increment_usage_count_by_id_usage_limit_reached(
    faker: Faker,
    active_session: ActiveSession,
) -> None:
    usage_count: int = faker.pyint(min_value=1, max_value=100)

    async with active_session():
        promocode = await Promocode.create(
            **{
                **factories.PromocodeWithCodeInputFactory.build_python(),
                **factories.UnrestrictedPromocodeSettingsFactory.build_python(),
                "usage_count": usage_count,
                "usage_limit": faker.pyint(min_value=1, max_value=usage_count),
            }
        )

    async with active_session():
        assert (
            await Promocode.find_and_increment_usage_count_by_id(
                promocode_id=promocode.id,
            )
            is None
        )

    async with active_session():
        await promocode.delete()
