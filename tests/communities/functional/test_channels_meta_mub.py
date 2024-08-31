from typing import Any

import pytest
from respx import MockRouter
from starlette.testclient import TestClient

from app.common.config import API_KEY
from app.communities.models.board_channels_db import BoardChannel
from app.communities.models.channels_db import Channel, ChannelType
from app.communities.models.communities_db import Community
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.mock_stack import MockStack
from tests.common.polyfactory_ext import BaseModelFactory
from tests.common.respx_ext import assert_last_httpx_request
from tests.common.types import AnyJSON
from tests.communities.factories import ChannelInputFactory, ChannelPatchFactory

pytestmark = pytest.mark.anyio


async def test_channel_creation(
    posts_respx_mock: MockRouter,
    mub_client: TestClient,
    active_session: ActiveSession,
    community: Community,
    channel_parent_category_id: int | None,
    channel_parent_path: str,
    specific_channel_kind: ChannelType,
) -> None:
    if specific_channel_kind is ChannelType.POSTS:
        posts_bridge_mock = posts_respx_mock.post(
            path__regex=r"/post-channels/(?P<channel_id>\d+)/",
        ).respond(status_code=204)

    channel_data: AnyJSON = ChannelInputFactory.build_json(kind=specific_channel_kind)

    channel_id: int = assert_response(
        mub_client.post(
            f"/mub/community-service/{channel_parent_path}/channels/",
            json=channel_data,
        ),
        expected_code=201,
        expected_json={**channel_data, "id": int},
    ).json()["id"]

    if specific_channel_kind is ChannelType.POSTS:
        assert_last_httpx_request(
            posts_bridge_mock,
            expected_headers={"X-Api-Key": API_KEY},
            expected_path=f"/internal/post-service/post-channels/{channel_id}/",
            expected_json={"community_id": community.id},
        )
    elif specific_channel_kind is ChannelType.BOARD:
        async with active_session():
            assert await BoardChannel.find_first_by_id(channel_id) is not None

    async with active_session():
        channel = await Channel.find_first_by_id(channel_id)
        assert channel is not None
        assert channel.list_id == (community.id, channel_parent_category_id)
        await channel.delete()


@pytest.mark.parametrize(
    "limit_field_name",
    [
        pytest.param("max_count_per_community", id="per_community"),
        pytest.param("max_count_per_category", id="per_category"),
    ],
)
async def test_channel_creation_quantity_exceeded(
    mock_stack: MockStack,
    mub_client: TestClient,
    channel_data: AnyJSON,
    channel_parent_path: str,
    limit_field_name: str,
) -> None:
    mock_stack.enter_mock(Channel, limit_field_name, property_value=0)
    assert_response(
        mub_client.post(
            f"/mub/community-service/{channel_parent_path}/channels/",
            json=channel_data,
        ),
        expected_code=409,
        expected_json={"detail": "Quantity exceeded"},
    )


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
    posts_respx_mock: MockRouter,
    mub_client: TestClient,
    active_session: ActiveSession,
    specific_channel_kind: ChannelType,
    specific_channel: Channel,
) -> None:
    if specific_channel_kind is ChannelType.POSTS:
        posts_bridge_mock = posts_respx_mock.delete(
            path=f"/post-channels/{specific_channel.id}/",
        ).respond(status_code=204)

    assert_nodata_response(
        mub_client.delete(f"/mub/community-service/channels/{specific_channel.id}/")
    )

    if specific_channel_kind is ChannelType.POSTS:
        assert_last_httpx_request(
            posts_bridge_mock,
            expected_headers={"X-Api-Key": API_KEY},
        )

    async with active_session():
        assert (await Channel.find_first_by_id(specific_channel.id)) is None


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
