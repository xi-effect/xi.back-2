from typing import Any

import pytest
from pydantic_marshals.contains import assert_contains
from starlette.testclient import TestClient

from app.communities.models.channels_db import Channel
from app.communities.models.communities_db import Community
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.mock_stack import MockStack
from tests.common.polyfactory_ext import BaseModelFactory
from tests.common.types import AnyJSON
from tests.communities.factories import ChannelPatchFactory

pytestmark = pytest.mark.anyio


async def test_channel_creation(
    mock_stack: MockStack,
    mub_client: TestClient,
    community: Community,
    channel_raw_data: AnyJSON,
    channel_data: AnyJSON,
    channel: Channel,
    channel_parent_category_id: int | None,
) -> None:
    channel_svc_mock = mock_stack.enter_async_mock(
        "app.communities.services.channels_svc.create_channel", return_value=channel
    )

    assert_response(
        mub_client.post(
            f"/mub/community-service/communities/{community.id}/channels/",
            params=(
                None
                if channel_parent_category_id is None
                else {"category_id": channel_parent_category_id}
            ),
            json=channel_data,
        ),
        expected_code=201,
        expected_json={**channel_data, "id": channel.id},
    )

    channel_svc_mock.assert_called_once_with(
        community_id=community.id,
        category_id=channel_parent_category_id,
        data=channel_raw_data,
    )


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
    community: Community,
    channel_data: AnyJSON,
    channel_parent_category_id: int | None,
    limit_field_name: str,
) -> None:
    mock_stack.enter_mock(Channel, limit_field_name, property_value=0)
    assert_response(
        mub_client.post(
            f"/mub/community-service/communities/{community.id}/channels/",
            params=(
                None
                if channel_parent_category_id is None
                else {"category_id": channel_parent_category_id}
            ),
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
    mock_stack: MockStack,
    mub_client: TestClient,
    channel_raw_data: Channel.InputSchema,
    channel: Channel,
) -> None:
    channel_svc_mock = mock_stack.enter_async_mock(
        "app.communities.services.channels_svc.delete_channel"
    )

    assert_nodata_response(
        mub_client.delete(f"/mub/community-service/channels/{channel.id}/")
    )

    channel_svc_mock.assert_called_once()
    assert_contains(
        channel_svc_mock.mock_calls[0].kwargs,
        {"channel": {**channel_raw_data.model_dump(), "id": channel.id}},
    )


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
