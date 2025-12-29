from collections.abc import AsyncIterator

import pytest
from faker import Faker
from starlette.testclient import TestClient

from app.subscriptions.models.promocodes_db import Promocode
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_response
from tests.subscriptions.factories import LimitedPromocodeInputFactory

pytestmark = pytest.mark.anyio

PROMOCODES_LIST_SIZE = 6


@pytest.fixture()
async def promocodes(
    faker: Faker,
    active_session: ActiveSession,
) -> AsyncIterator[list[Promocode]]:
    async with active_session():
        promocodes: list[Promocode] = [
            await Promocode.create(
                **LimitedPromocodeInputFactory.build_python(
                    code=faker.pystr(min_chars=4 + i, max_chars=4 + i)
                )
            )
            for i in range(PROMOCODES_LIST_SIZE)
        ]

    promocodes.sort(key=lambda promocode: promocode.created_at, reverse=True)

    yield promocodes

    async with active_session():
        for promocode in promocodes:
            await promocode.delete()


@pytest.mark.parametrize(
    ("offset", "limit"),
    [
        pytest.param(0, PROMOCODES_LIST_SIZE, id="start_to_end"),
        pytest.param(
            PROMOCODES_LIST_SIZE // 2, PROMOCODES_LIST_SIZE, id="middle_to_end"
        ),
        pytest.param(0, PROMOCODES_LIST_SIZE // 2, id="start_to_middle"),
    ],
)
async def test_promocodes_listing(
    mub_client: TestClient,
    promocodes: list[Promocode],
    offset: int,
    limit: int,
) -> None:
    assert_response(
        mub_client.get(
            "/mub/subscription-service/promocodes/",
            params={"offset": offset, "limit": limit},
        ),
        expected_json=[
            Promocode.ResponseSchema.model_validate(
                promocode, from_attributes=True
            ).model_dump(mode="json")
            for promocode in promocodes[offset:limit]
        ],
    )
