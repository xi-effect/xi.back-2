from typing import Any

import pytest
from starlette.testclient import TestClient

from app.communities.models.categories_db import Category
from app.communities.models.communities_db import Community
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.mock_stack import MockStack
from tests.common.polyfactory_ext import BaseModelFactory
from tests.common.types import AnyJSON
from tests.communities.factories import CategoryPatchFactory

pytestmark = pytest.mark.anyio


async def test_category_creation(
    mub_client: TestClient,
    active_session: ActiveSession,
    community: Community,
    category_data: AnyJSON,
) -> None:
    category_id: int = assert_response(
        mub_client.post(
            f"/mub/community-service/communities/{community.id}/categories/",
            json=category_data,
        ),
        expected_code=201,
        expected_json={**category_data, "id": int},
    ).json()["id"]

    async with active_session():
        category = await Category.find_first_by_id(category_id)
        assert category is not None
        await category.delete()


async def test_category_creation_quantity_exceed(
    mock_stack: MockStack,
    mub_client: TestClient,
    community: Community,
    category_data: AnyJSON,
) -> None:
    mock_stack.enter_mock(Category, "max_count_per_community", property_value=0)
    assert_response(
        mub_client.post(
            f"/mub/community-service/communities/{community.id}/categories/",
            json=category_data,
        ),
        expected_code=409,
        expected_json={"detail": "Quantity exceeded"},
    )


async def test_category_retrieving(
    mub_client: TestClient,
    category: Community,
    category_data: AnyJSON,
) -> None:
    assert_response(
        mub_client.get(f"/mub/community-service/categories/{category.id}/"),
        expected_json={**category_data, "id": category.id},
    )


async def test_category_updating(
    mub_client: TestClient,
    category: Community,
    category_data: AnyJSON,
) -> None:
    category_patch_data = CategoryPatchFactory.build_json()

    assert_response(
        mub_client.patch(
            f"/mub/community-service/categories/{category.id}/",
            json=category_patch_data,
        ),
        expected_json={**category_data, **category_patch_data},
    )


async def test_category_deleting(
    mub_client: TestClient,
    active_session: ActiveSession,
    category: Category,
) -> None:
    assert_nodata_response(
        mub_client.delete(f"/mub/community-service/categories/{category.id}/")
    )

    async with active_session():
        assert (await Category.find_first_by_id(category.id)) is None


@pytest.mark.parametrize(
    ("method", "body_factory"),
    [
        pytest.param("GET", None, id="get"),
        pytest.param("PATCH", CategoryPatchFactory, id="patch"),
        pytest.param("DELETE", None, id="delete"),
    ],
)
async def test_category_not_finding(
    mub_client: TestClient,
    active_session: ActiveSession,
    deleted_category_id: int,
    method: str,
    body_factory: type[BaseModelFactory[Any]] | None,
) -> None:
    assert_response(
        mub_client.request(
            method,
            f"/mub/community-service/categories/{deleted_category_id}/",
            json=body_factory and body_factory.build_json(),
        ),
        expected_code=404,
        expected_json={"detail": "Category not found"},
    )
