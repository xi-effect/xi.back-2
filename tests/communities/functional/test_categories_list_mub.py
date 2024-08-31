from collections.abc import AsyncIterator

import pytest
from pydantic_marshals.contains import assert_contains
from starlette.testclient import TestClient

from app.communities.models.categories_db import Category
from app.communities.models.communities_db import Community
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.types import AnyJSON
from tests.communities import factories

pytestmark = pytest.mark.anyio


async def test_reindexing_categories(
    mub_client: TestClient,
    active_session: ActiveSession,
    community: Community,
) -> None:
    categories_count = 3
    async with active_session() as db_session:
        db_session.add_all(
            Category(
                community_id=community.id,
                position=i,
                **factories.CategoryInputFactory.build_json(),
            )
            for i in range(categories_count)
        )

    assert_nodata_response(
        mub_client.put(
            f"/mub/community-service/communities/{community.id}/categories/positions/"
        )
    )

    async with active_session():
        categories = await Category.find_all_by_community_id(community_id=community.id)
        positions = [category.position for category in categories]
        assert_contains(
            positions, [i * Category.spacing for i in range(categories_count)]
        )

        for category in categories:
            await category.delete()


CATEGORY_LIST_SIZE = 5


@pytest.fixture()
async def categories_data(
    active_session: ActiveSession,
    community: Community,
) -> AsyncIterator[list[AnyJSON]]:
    async with active_session():
        categories = [
            await Category.create(
                community_id=community.id,
                **factories.CategoryInputFactory.build_json(),
            )
            for _ in range(CATEGORY_LIST_SIZE)
        ]
    categories.sort(key=lambda category: category.position)

    yield [
        Category.ResponseSchema.model_validate(
            category, from_attributes=True
        ).model_dump(mode="json")
        for category in categories
    ]

    async with active_session():
        for category in categories:
            await category.delete()


async def test_categories_listing(
    mub_client: TestClient,
    community: Community,
    categories_data: list[AnyJSON],
) -> None:
    assert_response(
        mub_client.get(
            f"/mub/community-service/communities/{community.id}/categories/"
        ),
        expected_json=categories_data,
    )


@pytest.mark.parametrize(
    ("target", "after", "before"),
    [
        pytest.param(2, None, 0, id="middle_to_start"),
        pytest.param(2, CATEGORY_LIST_SIZE - 1, None, id="middle_to_end"),
        pytest.param(0, 2, 3, id="start_to_middle"),
    ],
)
async def test_category_moving(
    mub_client: TestClient,
    active_session: ActiveSession,
    community: Community,
    categories_data: list[AnyJSON],
    target: int,
    after: int | None,
    before: int | None,
) -> None:
    category_ids = [category_data["id"] for category_data in categories_data]

    assert_nodata_response(
        mub_client.put(
            f"/mub/community-service/categories/{category_ids[target]}/position/",
            json={
                "after_id": None if after is None else category_ids[after],
                "before_id": None if before is None else category_ids[before],
            },
        ),
    )

    if before is None:
        category_ids.append(category_ids.pop(target))
    elif target < before:
        category_ids.insert(before - 1, category_ids.pop(target))
    else:
        category_ids.insert(before, category_ids.pop(target))

    async with active_session():
        assert [  # noqa: WPS309  # WPS bug
            category.id
            for category in await Category.find_all_by_community_id(
                community_id=community.id
            )
        ] == category_ids
