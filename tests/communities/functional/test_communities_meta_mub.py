from typing import Any

import pytest
from starlette import status
from starlette.testclient import TestClient

from app.communities.models.communities_db import Community
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.polyfactory_ext import BaseModelFactory
from tests.common.types import AnyJSON
from tests.communities.factories import CommunityFullPatchFactory

pytestmark = pytest.mark.anyio


async def test_community_creation(
    mub_client: TestClient,
    active_session: ActiveSession,
    community_data: AnyJSON,
) -> None:
    community_id: int = assert_response(
        mub_client.post("/mub/community-service/communities/", json=community_data),
        expected_code=status.HTTP_201_CREATED,
        expected_json={**community_data, "id": int},
    ).json()["id"]

    async with active_session():
        community = await Community.find_first_by_id(community_id)
        assert community is not None
        await community.delete()


async def test_community_retrieving(
    mub_client: TestClient,
    community_data: AnyJSON,
    community: Community,
) -> None:
    assert_response(
        mub_client.get(f"/mub/community-service/communities/{community.id}/"),
        expected_json={**community_data},
    )


async def test_community_updating(
    mub_client: TestClient,
    community: Community,
    community_data: AnyJSON,
) -> None:
    community_patch_data = CommunityFullPatchFactory.build_json()

    assert_response(
        mub_client.patch(
            f"/mub/community-service/communities/{community.id}/",
            json=community_patch_data,
        ),
        expected_json={**community_data, **community_patch_data},
    )


async def test_community_deleting(
    mub_client: TestClient,
    active_session: ActiveSession,
    community: Community,
) -> None:
    assert_nodata_response(
        mub_client.delete(f"/mub/community-service/communities/{community.id}/")
    )

    async with active_session():
        assert (await Community.find_first_by_id(community.id)) is None


@pytest.mark.parametrize(
    ("method", "body_factory"),
    [
        pytest.param("GET", None, id="get"),
        pytest.param("PATCH", CommunityFullPatchFactory, id="patch"),
        pytest.param("DELETE", None, id="delete"),
    ],
)
async def test_community_not_finding(
    mub_client: TestClient,
    active_session: ActiveSession,
    deleted_community_id: int,
    method: str,
    body_factory: type[BaseModelFactory[Any]] | None,
) -> None:
    assert_response(
        mub_client.request(
            method,
            f"/mub/community-service/communities/{deleted_community_id}/",
            json=body_factory and body_factory.build_json(),
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Community not found"},
    )
