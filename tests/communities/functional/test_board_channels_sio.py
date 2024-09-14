import pytest

from app.communities.models.board_channels_db import BoardChannel
from app.communities.models.communities_db import Community
from tests.common.tmexio_testing import TMEXIOTestClient, assert_ack

pytestmark = pytest.mark.anyio


async def test_board_channel_retrieving(
    community: Community,
    tmexio_actor_client: TMEXIOTestClient,
    board_channel: BoardChannel,
) -> None:
    assert_ack(
        await tmexio_actor_client.emit(
            "retrieve-board-channel",
            community_id=community.id,
            channel_id=board_channel.id,
        ),
        expected_data={"hoku_id": board_channel.hoku_id},
    )
    tmexio_actor_client.assert_no_more_events()


async def test_board_channel_retrieving_board_channel_not_found(
    community: Community,
    tmexio_actor_client: TMEXIOTestClient,
    deleted_board_channel_id: int,
) -> None:
    assert_ack(
        await tmexio_actor_client.emit(
            "retrieve-board-channel",
            community_id=community.id,
            channel_id=deleted_board_channel_id,
        ),
        expected_code=404,
        expected_data="Board-channel not found",
    )
    tmexio_actor_client.assert_no_more_events()


async def test_board_channel_retrieving_community_not_found(
    deleted_community_id: int,
    tmexio_outsider_client: TMEXIOTestClient,
) -> None:
    assert_ack(
        await tmexio_outsider_client.emit(
            "retrieve-board-channel",
            community_id=deleted_community_id,
            channel_id=1,
        ),
        expected_code=404,
        expected_data="Community not found",
    )
    tmexio_outsider_client.assert_no_more_events()


async def test_board_channel_retrieving_no_access_to_community(
    community: Community,
    tmexio_outsider_client: TMEXIOTestClient,
) -> None:
    assert_ack(
        await tmexio_outsider_client.emit(
            "retrieve-board-channel",
            community_id=community.id,
            channel_id=1,
        ),
        expected_code=403,
        expected_data="No access to community",
    )
    tmexio_outsider_client.assert_no_more_events()
