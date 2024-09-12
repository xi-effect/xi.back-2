from uuid import uuid4

import pytest
from respx import MockRouter

from app.common.config import API_KEY
from app.communities.models.board_channels_db import BoardChannel
from app.communities.models.channels_db import Channel, ChannelType
from app.communities.models.communities_db import Community
from app.communities.services import channels_svc
from tests.common.active_session import ActiveSession
from tests.common.respx_ext import assert_last_httpx_request
from tests.communities import factories

pytestmark = pytest.mark.anyio


async def test_post_channel_deletion(
    active_session: ActiveSession,
    posts_respx_mock: MockRouter,
    community: Community,
    channel_parent_category_id: int | None,
) -> None:
    channel_raw_data: Channel.InputSchema = factories.ChannelInputFactory.build(
        kind=ChannelType.POSTS
    )

    async with active_session():
        channel = await Channel.create(
            community_id=community.id,
            category_id=channel_parent_category_id,
            **channel_raw_data.model_dump(),
        )

    posts_bridge_mock = posts_respx_mock.delete(
        path=f"/post-channels/{channel.id}/",
    ).respond(status_code=204)

    async with active_session() as session:
        session.add(channel)
        await session.refresh(channel)
        await channels_svc.delete_channel(channel=channel)

    async with active_session():
        assert (await Channel.find_first_by_id(channel.id)) is None

    assert_last_httpx_request(
        posts_bridge_mock,
        expected_headers={"X-Api-Key": API_KEY},
    )


async def test_board_channel_deletion(
    active_session: ActiveSession,
    storage_respx_mock: MockRouter,
    community: Community,
    channel_parent_category_id: int | None,
) -> None:
    channel_raw_data: Channel.InputSchema = factories.ChannelInputFactory.build(
        kind=ChannelType.BOARD
    )

    async with active_session():
        channel = await Channel.create(
            community_id=community.id,
            category_id=channel_parent_category_id,
            **channel_raw_data.model_dump(),
        )

        board_channel = await BoardChannel.create(
            id=channel.id,
            access_group_id=str(uuid4()),
            hoku_id=str(uuid4()),
        )

    delete_access_group_mock = storage_respx_mock.delete(
        path=f"/access-groups/{board_channel.access_group_id}/"
    ).respond(status_code=204)

    async with active_session() as session:
        session.add(channel)
        await session.refresh(channel)
        await channels_svc.delete_channel(channel=channel)

    async with active_session():
        assert (await Channel.find_first_by_id(channel.id)) is None

    assert_last_httpx_request(
        delete_access_group_mock,
        expected_headers={"X-Api-Key": API_KEY},
    )


@pytest.mark.parametrize(
    "channel_kind", [ChannelType.TASKS, ChannelType.CHAT, ChannelType.CALL]
)
async def test_simple_channel_deletion(
    active_session: ActiveSession,
    community: Community,
    channel_parent_category_id: int | None,
    channel_kind: ChannelType,
) -> None:
    channel_raw_data: Channel.InputSchema = factories.ChannelInputFactory.build(
        kind=channel_kind
    )

    async with active_session():
        channel = await Channel.create(
            community_id=community.id,
            category_id=channel_parent_category_id,
            **channel_raw_data.model_dump(),
        )

    async with active_session() as session:
        session.add(channel)
        await session.refresh(channel)
        await channels_svc.delete_channel(channel=channel)

    async with active_session():
        assert (await Channel.find_first_by_id(channel.id)) is None
