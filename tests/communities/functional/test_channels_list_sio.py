import pytest
from starlette import status

from app.communities.models.categories_db import Category
from app.communities.models.channels_db import Channel
from app.communities.models.communities_db import Community
from tests.common.active_session import ActiveSession
from tests.common.tmexio_testing import TMEXIOTestClient, assert_ack
from tests.common.types import AnyJSON
from tests.communities.conftest import CHANNEL_LIST_SIZE

pytestmark = pytest.mark.anyio


async def test_channels_listing(
    community: Community,
    tmexio_participant_client: TMEXIOTestClient,
    category_data: AnyJSON,
    category: Category,
    channels_without_category_data: list[AnyJSON],
    channels_with_category_data: list[AnyJSON],
) -> None:
    assert_ack(
        await tmexio_participant_client.emit(
            "list-channels",
            community_id=community.id,
        ),
        expected_data=[
            {
                "category": None,
                "channels": channels_without_category_data,
            },
            {
                "category": {**category_data, "id": category.id},
                "channels": channels_with_category_data,
            },
        ],
    )
    tmexio_participant_client.assert_no_more_events()


@pytest.mark.parametrize(
    ("target", "after", "before"),
    [
        pytest.param(2, None, 0, id="middle_to_start"),
        pytest.param(2, CHANNEL_LIST_SIZE - 1, None, id="middle_to_end"),
        pytest.param(0, 2, 3, id="start_to_middle"),
    ],
)
async def test_channel_moving(
    active_session: ActiveSession,
    community: Community,
    community_room_listener: TMEXIOTestClient,
    tmexio_owner_client: TMEXIOTestClient,
    channels_without_category_data: list[AnyJSON],
    channels_with_category_data: list[AnyJSON],
    channel_parent_category_id: int | None,
    target: int,
    after: int | None,
    before: int | None,
) -> None:
    channels_data = list(
        channels_without_category_data
        if channel_parent_category_id is None
        else channels_with_category_data
    )
    channel_ids = [channel_data["id"] for channel_data in channels_data]

    assert_ack(
        await tmexio_owner_client.emit(
            "move-channel",
            community_id=community.id,
            channel_id=channel_ids[target],
            category_id=channel_parent_category_id,
            after_id=None if after is None else channel_ids[after],
            before_id=None if before is None else channel_ids[before],
        ),
        expected_code=status.HTTP_204_NO_CONTENT,
    )
    tmexio_owner_client.assert_no_more_events()

    community_room_listener.assert_next_event(
        expected_name="move-channel",
        expected_data={
            "community_id": community.id,
            "channel_id": channel_ids[target],
            "category_id": channel_parent_category_id,
            "after_id": None if after is None else channel_ids[after],
            "before_id": None if before is None else channel_ids[before],
        },
    )
    community_room_listener.assert_no_more_events()

    if before is None:
        channel_ids.append(channel_ids.pop(target))
    elif target < before:
        channel_ids.insert(before - 1, channel_ids.pop(target))
    else:
        channel_ids.insert(before, channel_ids.pop(target))

    async with active_session():
        assert [  # noqa: WPS309  # WPS bug
            channel.id
            for channel in await Channel.find_all_by_kwargs(
                Channel.position,
                community_id=community.id,
                category_id=channel_parent_category_id,
            )
        ] == channel_ids


async def test_channel_moving_category_not_found(
    community: Community,
    tmexio_owner_client: TMEXIOTestClient,
    deleted_category_id: int,
    channel: Channel,
) -> None:
    assert_ack(
        await tmexio_owner_client.emit(
            "move-channel",
            community_id=community.id,
            channel_id=channel.id,
            category_id=deleted_category_id,
            after_id=None,
            before_id=None,
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_data="Category not found",
    )
    tmexio_owner_client.assert_no_more_events()


async def test_channel_moving_channel_not_found(
    community: Community,
    tmexio_owner_client: TMEXIOTestClient,
    deleted_channel_id: int,
) -> None:
    assert_ack(
        await tmexio_owner_client.emit(
            "move-channel",
            community_id=community.id,
            channel_id=deleted_channel_id,
            category_id=1,
            after_id=None,
            before_id=None,
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_data="Channel not found",
    )
    tmexio_owner_client.assert_no_more_events()


async def test_channel_moving_not_sufficient_permissions(
    community: Community,
    tmexio_participant_client: TMEXIOTestClient,
    channel: Channel,
) -> None:
    assert_ack(
        await tmexio_participant_client.emit(
            "move-channel",
            community_id=community.id,
            channel_id=channel.id,
            category_id=1,
            after_id=None,
            before_id=None,
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_data="Not sufficient permissions",
    )
    tmexio_participant_client.assert_no_more_events()


@pytest.mark.parametrize(
    "event_name",
    [
        pytest.param("list-channels", id="list"),
        pytest.param("move-channel", id="move"),
    ],
)
async def test_channels_requesting_community_not_finding(
    deleted_community_id: int,
    tmexio_outsider_client: TMEXIOTestClient,
    event_name: str,
) -> None:
    assert_ack(
        await tmexio_outsider_client.emit(
            event_name,
            community_id=deleted_community_id,
            channel_id=1,
            category_id=1,
            after_id=None,
            before_id=None,
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_data="Community not found",
    )
    tmexio_outsider_client.assert_no_more_events()


@pytest.mark.parametrize(
    "event_name",
    [
        pytest.param("list-channels", id="list"),
        pytest.param("move-channel", id="move"),
    ],
)
async def test_channels_requesting_no_access_to_community(
    community: Community,
    tmexio_outsider_client: TMEXIOTestClient,
    channel: Channel,
    channel_parent_category_id: int | None,
    event_name: str,
) -> None:
    assert_ack(
        await tmexio_outsider_client.emit(
            event_name,
            community_id=community.id,
            channel_id=channel.id,
            category_id=channel_parent_category_id,
            after_id=None,
            before_id=None,
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_data="No access to community",
    )
    tmexio_outsider_client.assert_no_more_events()
