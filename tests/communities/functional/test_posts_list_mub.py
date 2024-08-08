from collections.abc import AsyncIterator

import pytest
from starlette.testclient import TestClient

from app.communities.models.channels_db import Channel, ChannelType
from app.communities.models.posts_db import Post
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_response
from tests.common.types import AnyJSON
from tests.communities.conftest import change_channel_kind
from tests.communities.factories import PostInputFactory

pytestmark = pytest.mark.anyio

POST_LIST_SIZE = 6


@pytest.fixture()
async def posts(
    active_session: ActiveSession,
    channel: Channel,
) -> AsyncIterator[list[Post]]:
    posts_data: list[AnyJSON] = [
        PostInputFactory.build_json() for _ in range(POST_LIST_SIZE)
    ]

    async with active_session():
        posts = [
            await Post.create(channel_id=channel.id, **post_data)
            for post_data in posts_data
        ]
    posts.sort(key=lambda post: post.created_at, reverse=True)

    yield posts

    async with active_session():
        for post in posts:
            await post.delete()


@pytest.mark.parametrize(
    ("offset", "limit"),
    [
        pytest.param(0, POST_LIST_SIZE, id="start_to_end"),
        pytest.param(POST_LIST_SIZE // 2, POST_LIST_SIZE, id="middle_to_end"),
        pytest.param(0, POST_LIST_SIZE // 2, id="start_to_middle"),
    ],
)
async def test_posts_listing(
    active_session: ActiveSession,
    mub_client: TestClient,
    channel: Channel,
    posts: list[Post],
    offset: int,
    limit: int,
) -> None:
    await change_channel_kind(active_session, channel.id, ChannelType.POSTS)

    assert_response(
        mub_client.get(
            f"/mub/community-service/channels/{channel.id}/posts/",
            params={"offset": offset, "limit": limit},
        ),
        expected_json=[
            Post.ResponseSchema(**posts[i].__dict__).model_dump(mode="json")
            for i in range(offset, limit)
        ],
    )


@pytest.mark.parametrize(
    "kind",
    [
        pytest.param(ChannelType.TASKS, id="tasks"),
        pytest.param(ChannelType.CHAT, id="chat"),
        pytest.param(ChannelType.CALL, id="call"),
        pytest.param(ChannelType.BOARD, id="board"),
    ],
)
async def test_posts_listing_invalid_channel_kind(
    active_session: ActiveSession,
    mub_client: TestClient,
    channel: Channel,
    kind: ChannelType,
) -> None:
    await change_channel_kind(active_session, channel.id, kind)

    assert_response(
        mub_client.get(
            f"/mub/community-service/channels/{channel.id}/posts/",
            params={"offset": 0, "limit": POST_LIST_SIZE},
        ),
        expected_code=409,
        expected_json={"detail": "Invalid channel kind"},
    )
