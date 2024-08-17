from collections.abc import AsyncIterator

import pytest
from starlette.testclient import TestClient

from app.posts.models.post_channels_db import PostChannel
from app.posts.models.posts_db import Post
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_response
from tests.common.types import AnyJSON
from tests.posts.factories import PostInputFactory

pytestmark = pytest.mark.anyio

POST_LIST_SIZE = 6


@pytest.fixture()
async def posts(
    active_session: ActiveSession,
    post_channel: PostChannel,
) -> AsyncIterator[list[Post]]:
    posts_data: list[AnyJSON] = [
        PostInputFactory.build_json() for _ in range(POST_LIST_SIZE)
    ]

    async with active_session():
        posts = [
            await Post.create(channel_id=post_channel.id, **post_data)
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
    post_channel: PostChannel,
    posts: list[Post],
    offset: int,
    limit: int,
) -> None:
    assert_response(
        mub_client.get(
            f"/mub/post-service/post-channels/{post_channel.id}/posts/",
            params={"offset": offset, "limit": limit},
        ),
        expected_json=[
            Post.ResponseSchema(**posts[i].__dict__).model_dump(mode="json")
            for i in range(offset, limit)
        ],
    )


async def test_posts_listing_post_channel_not_found(
    active_session: ActiveSession,
    mub_client: TestClient,
    deleted_post_channel_id: int,
) -> None:
    assert_response(
        mub_client.get(
            f"/mub/post-service/post-channels/{deleted_post_channel_id}/posts/",
            params={"offset": 0, "limit": POST_LIST_SIZE},
        ),
        expected_code=404,
        expected_json={"detail": "Post-channel not found"},
    )
