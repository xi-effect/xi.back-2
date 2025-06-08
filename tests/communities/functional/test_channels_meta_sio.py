from typing import Any

import pytest
from pydantic_marshals.contains import assert_contains
from starlette import status

from app.communities.models.categories_db import Category
from app.communities.models.channels_db import Channel
from app.communities.models.communities_db import Community
from tests.common.mock_stack import MockStack
from tests.common.polyfactory_ext import BaseModelFactory
from tests.common.tmexio_testing import TMEXIOTestClient, assert_ack
from tests.common.types import AnyJSON
from tests.communities.factories import ChannelInputFactory, ChannelPatchFactory

pytestmark = pytest.mark.anyio


async def test_channel_creation(
    mock_stack: MockStack,
    community: Community,
    community_room_listener: TMEXIOTestClient,
    tmexio_owner_client: TMEXIOTestClient,
    channel_raw_data: AnyJSON,
    channel_data: AnyJSON,
    channel: Channel,
    channel_parent_category_id: int | None,
) -> None:
    channel_svc_mock = mock_stack.enter_async_mock(
        "app.communities.services.channels_svc.create_channel", return_value=channel
    )

    assert_ack(
        await tmexio_owner_client.emit(
            "create-channel",
            community_id=community.id,
            category_id=channel_parent_category_id,
            data=channel_data,
        ),
        expected_code=201,
        expected_data={**channel_data, "id": channel.id},
    )

    community_room_listener.assert_next_event(
        expected_name="create-channel",
        expected_data={**channel_data, "id": int},
    )
    community_room_listener.assert_no_more_events()

    channel_svc_mock.assert_called_once_with(
        community_id=community.id,
        category_id=channel_parent_category_id,
        data=channel_raw_data,
    )


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
        expected_code=status.HTTP_404_NOT_FOUND,
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
        expected_code=status.HTTP_409_CONFLICT,
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
    mock_stack: MockStack,
    community: Community,
    community_room_listener: TMEXIOTestClient,
    tmexio_owner_client: TMEXIOTestClient,
    channel_raw_data: Channel.InputSchema,
    channel: Channel,
) -> None:
    channel_svc_mock = mock_stack.enter_async_mock(
        "app.communities.services.channels_svc.delete_channel"
    )

    assert_ack(
        await tmexio_owner_client.emit(
            "delete-channel",
            community_id=community.id,
            channel_id=channel.id,
        ),
        expected_code=204,
    )
    tmexio_owner_client.assert_no_more_events()

    community_room_listener.assert_next_event(
        expected_name="delete-channel",
        expected_data={"community_id": community.id, "channel_id": channel.id},
    )
    community_room_listener.assert_no_more_events()

    channel_svc_mock.assert_called_once()
    assert_contains(
        channel_svc_mock.mock_calls[0].kwargs,
        {"channel": {**channel_raw_data.model_dump(), "id": channel.id}},
    )


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
        expected_code=status.HTTP_404_NOT_FOUND,
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
        expected_code=status.HTTP_403_FORBIDDEN,
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
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_data="Not sufficient permissions",
    )
    tmexio_participant_client.assert_no_more_events()
