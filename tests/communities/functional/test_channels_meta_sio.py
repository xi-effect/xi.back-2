from typing import Any

import pytest
from respx import MockRouter

from app.common.config import API_KEY
from app.communities.models.board_channels_db import BoardChannel
from app.communities.models.categories_db import Category
from app.communities.models.channels_db import Channel, ChannelType
from app.communities.models.communities_db import Community
from tests.common.active_session import ActiveSession
from tests.common.mock_stack import MockStack
from tests.common.polyfactory_ext import BaseModelFactory
from tests.common.respx_ext import assert_last_httpx_request
from tests.common.tmexio_testing import TMEXIOTestClient, assert_ack
from tests.common.types import AnyJSON
from tests.communities.factories import ChannelInputFactory, ChannelPatchFactory

pytestmark = pytest.mark.anyio


async def test_channel_creation(
    posts_respx_mock: MockRouter,
    active_session: ActiveSession,
    community: Community,
    community_room_listener: TMEXIOTestClient,
    tmexio_owner_client: TMEXIOTestClient,
    specific_channel_kind: ChannelType,
    channel_parent_category_id: int | None,
) -> None:
    if specific_channel_kind is ChannelType.POSTS:
        posts_bridge_mock = posts_respx_mock.post(
            path__regex=r"/post-channels/(?P<channel_id>\d+)/",
        ).respond(status_code=204)

    channel_data: AnyJSON = ChannelInputFactory.build_json(kind=specific_channel_kind)

    channel_id: int = assert_ack(
        await tmexio_owner_client.emit(
            "create-channel",
            community_id=community.id,
            category_id=channel_parent_category_id,
            data=channel_data,
        ),
        expected_code=201,
        expected_data={**channel_data, "id": int},
    )[1]["id"]

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

    community_room_listener.assert_next_event(
        expected_name="create-channel",
        expected_data={**channel_data, "id": int},
    )
    community_room_listener.assert_no_more_events()

    async with active_session():
        channel = await Channel.find_first_by_id(channel_id)
        assert channel is not None
        assert channel.list_id == (community.id, channel_parent_category_id)
        await channel.delete()


async def test_channel_creation_category_not_found(
    community: Community,
    tmexio_owner_client: TMEXIOTestClient,
    deleted_category_id: int,
    channel_data: AnyJSON,
) -> None:
    assert_ack(
        await tmexio_owner_client.emit(
            "create-channel",
            community_id=community.id,
            category_id=deleted_category_id,
            data=channel_data,
        ),
        expected_code=404,
        expected_data="Category not found",
    )
    tmexio_owner_client.assert_no_more_events()


@pytest.mark.parametrize(
    ("limit_field_name", "expected_message"),
    [
        pytest.param(
            "max_count_per_community",
            "Quantity limit per community exceeded",
            id="per_community",
        ),
        pytest.param(
            "max_count_per_category",
            "Quantity limit per category exceeded",
            id="per_category",
        ),
    ],
)
async def test_channel_creation_quantity_exceeded(
    mock_stack: MockStack,
    community: Community,
    tmexio_owner_client: TMEXIOTestClient,
    category: Category,
    channel_data: AnyJSON,
    limit_field_name: str,
    expected_message: str,
) -> None:
    mock_stack.enter_mock(Channel, limit_field_name, property_value=0)

    assert_ack(
        await tmexio_owner_client.emit(
            "create-channel",
            community_id=community.id,
            category_id=category.id,
            data=channel_data,
        ),
        expected_code=409,
        expected_data=expected_message,
    )
    tmexio_owner_client.assert_no_more_events()


async def test_channel_updating(
    community: Community,
    community_room_listener: TMEXIOTestClient,
    tmexio_owner_client: TMEXIOTestClient,
    channel_data: AnyJSON,
    channel: Channel,
) -> None:
    channel_patch_data = ChannelPatchFactory.build_json()

    assert_ack(
        await tmexio_owner_client.emit(
            "update-channel",
            community_id=community.id,
            channel_id=channel.id,
            data=channel_patch_data,
        ),
        expected_data={**channel_data, **channel_patch_data, "id": channel.id},
    )
    tmexio_owner_client.assert_no_more_events()

    community_room_listener.assert_next_event(
        expected_name="update-channel",
        expected_data={**channel_data, **channel_patch_data, "id": channel.id},
    )
    community_room_listener.assert_no_more_events()


async def test_channel_deleting(
    posts_respx_mock: MockRouter,
    active_session: ActiveSession,
    community: Community,
    community_room_listener: TMEXIOTestClient,
    tmexio_owner_client: TMEXIOTestClient,
    specific_channel_kind: ChannelType,
    specific_channel: Channel,
) -> None:
    if specific_channel_kind is ChannelType.POSTS:
        posts_bridge_mock = posts_respx_mock.delete(
            path=f"/post-channels/{specific_channel.id}/",
        ).respond(status_code=204)

    assert_ack(
        await tmexio_owner_client.emit(
            "delete-channel",
            community_id=community.id,
            channel_id=specific_channel.id,
        ),
        expected_code=204,
    )
    tmexio_owner_client.assert_no_more_events()

    community_room_listener.assert_next_event(
        expected_name="delete-channel",
        expected_data={"community_id": community.id, "channel_id": specific_channel.id},
    )
    community_room_listener.assert_no_more_events()

    if specific_channel_kind is ChannelType.POSTS:
        assert_last_httpx_request(
            posts_bridge_mock,
            expected_headers={"X-Api-Key": API_KEY},
        )

    async with active_session():
        assert (await Channel.find_first_by_id(specific_channel.id)) is None


@pytest.mark.parametrize(
    ("event_name", "data_factory"),
    [
        pytest.param("create-channel", ChannelInputFactory, id="create"),
        pytest.param("update-channel", ChannelPatchFactory, id="update"),
        pytest.param("delete-channel", None, id="delete"),
    ],
)
async def test_channels_requesting_community_not_finding(
    deleted_community_id: int,
    tmexio_outsider_client: TMEXIOTestClient,
    event_name: str,
    data_factory: type[BaseModelFactory[Any]] | None,
) -> None:
    assert_ack(
        await tmexio_outsider_client.emit(
            event_name,
            community_id=deleted_community_id,
            channel_id=1,
            category_id=1,
            data=data_factory and data_factory.build_json(),
        ),
        expected_code=404,
        expected_data="Community not found",
    )
    tmexio_outsider_client.assert_no_more_events()


@pytest.mark.parametrize(
    ("event_name", "data_factory"),
    [
        pytest.param("create-channel", ChannelInputFactory, id="create"),
        pytest.param("update-channel", ChannelPatchFactory, id="update"),
        pytest.param("delete-channel", None, id="delete"),
    ],
)
async def test_channels_requesting_no_access_to_community(
    community: Community,
    tmexio_outsider_client: TMEXIOTestClient,
    channel: Channel,
    event_name: str,
    data_factory: type[BaseModelFactory[Any]] | None,
) -> None:
    assert_ack(
        await tmexio_outsider_client.emit(
            event_name,
            community_id=community.id,
            channel_id=channel.id,
            category_id=channel.category_id,
            data=data_factory and data_factory.build_json(),
        ),
        expected_code=403,
        expected_data="No access to community",
    )
    tmexio_outsider_client.assert_no_more_events()


@pytest.mark.parametrize(
    ("event_name", "data_factory"),
    [
        pytest.param("create-channel", ChannelInputFactory, id="create"),
        pytest.param("update-channel", ChannelPatchFactory, id="update"),
        pytest.param("delete-channel", None, id="delete"),
    ],
)
async def test_channels_requesting_not_sufficient_permissions(
    community: Community,
    tmexio_participant_client: TMEXIOTestClient,
    channel: Channel,
    event_name: str,
    data_factory: type[BaseModelFactory[Any]] | None,
) -> None:
    assert_ack(
        await tmexio_participant_client.emit(
            event_name,
            community_id=community.id,
            channel_id=channel.id,
            category_id=channel.category_id,
            data=data_factory and data_factory.build_json(),
        ),
        expected_code=403,
        expected_data="Not sufficient permissions",
    )
    tmexio_participant_client.assert_no_more_events()
