import pytest
from starlette.testclient import TestClient

from app.communities.models.communities_db import Community
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_response
from tests.common.types import AnyJSON

pytestmark = pytest.mark.anyio


async def test_community_creation(
    mub_client: TestClient,
    active_session: ActiveSession,
    community_data: AnyJSON,
) -> None:
    community_id: int = assert_response(
        mub_client.post("/mub/communities/", json=community_data),
        expected_code=201,
        expected_json={**community_data, "id": int},
    ).json()["id"]

    async with active_session():
        community = await Community.find_first_by_id(community_id)
        assert community is not None
        await community.delete()
