from typing import Any

import pytest
from starlette.testclient import TestClient

from app.communities.models.categories_db import Category
from app.communities.models.channels_db import Channel
from app.communities.models.communities_db import Community
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.polyfactory_ext import BaseModelFactory
from tests.common.types import AnyJSON
from tests.communities.factories import ChannelPatchFactory

pytestmark = pytest.mark.anyio


async def test_channel_creation(
    mub_client: TestClient,
    active_session: ActiveSession,
    community: Community,
    channel_data: AnyJSON,
) -> None:
    channel_id: int = assert_response(
        mub_client.post(
            f"/mub/community-service/communities/{community.id}/channels/",
            json=channel_data,
        ),
        expected_code=201,
        expected_json={**channel_data, "id": int},
    ).json()["id"]

    async with active_session():
        channel = await Channel.find_first_by_id(channel_id)
        assert channel is not None
        assert channel.list_id == (community.id, None)
        await channel.delete()


async def test_channel_in_category_creation(
    mub_client: TestClient,
    active_session: ActiveSession,
    category: Category,
    channel_data: AnyJSON,
) -> None:
    channel_id: int = assert_response(
        mub_client.post(
            f"/mub/community-service/categories/{category.id}/channels/",
            json=channel_data,
        ),
        expected_code=201,
        expected_json={**channel_data, "id": int},
    ).json()["id"]

    async with active_session():
        channel = await Channel.find_first_by_id(channel_id)
        assert channel is not None
        assert channel.list_id == (category.community_id, category.id)
        await channel.delete()


async def test_channel_retrieving(
    mub_client: TestClient,
    channel: Community,
    channel_data: AnyJSON,
) -> None:
    assert_response(
        mub_client.get(f"/mub/community-service/channels/{channel.id}/"),
        expected_json={**channel_data, "id": channel.id},
    )


async def test_channel_updating(
    mub_client: TestClient,
    channel: Community,
    channel_data: AnyJSON,
) -> None:
    channel_patch_data = ChannelPatchFactory.build_json()

    assert_response(
        mub_client.patch(
            f"/mub/community-service/channels/{channel.id}/",
            json=channel_patch_data,
        ),
        expected_json={**channel_data, **channel_patch_data},
    )


async def test_channel_deleting(
    mub_client: TestClient,
    active_session: ActiveSession,
    channel: Channel,
) -> None:
    assert_nodata_response(
        mub_client.delete(f"/mub/community-service/channels/{channel.id}/")
    )

    async with active_session():
        assert (await Channel.find_first_by_id(channel.id)) is None


@pytest.mark.parametrize(
    ("method", "body_factory"),
    [
        pytest.param("GET", None, id="get"),
        pytest.param("PATCH", ChannelPatchFactory, id="patch"),
        pytest.param("DELETE", None, id="delete"),
    ],
)
async def test_channel_not_finding(
    mub_client: TestClient,
    active_session: ActiveSession,
    deleted_channel_id: int,
    method: str,
    body_factory: type[BaseModelFactory[Any]] | None,
) -> None:
    assert_response(
        mub_client.request(
            method,
            f"/mub/community-service/channels/{deleted_channel_id}/",
            json=body_factory and body_factory.build_json(),
        ),
        expected_code=404,
        expected_json={"detail": "Channel not found"},
    )
