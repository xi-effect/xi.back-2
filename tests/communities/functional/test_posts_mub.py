from typing import Any

import pytest
from starlette.testclient import TestClient

from app.communities.models.channels_db import Channel, ChannelType
from app.communities.models.posts_db import Post
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.polyfactory_ext import BaseModelFactory
from tests.common.types import AnyJSON
from tests.communities.conftest import change_channel_kind
from tests.communities.factories import PostInputFactory, PostPatchFactory

pytestmark = pytest.mark.anyio


async def test_post_creation(
    mub_client: TestClient,
    active_session: ActiveSession,
    channel: Channel,
) -> None:
    await change_channel_kind(active_session, channel.id, ChannelType.POSTS)

    post_input_data = PostInputFactory.build_json()
    post_id: int = assert_response(
        mub_client.post(
            f"/mub/community-service/channels/{channel.id}/posts/",
            json=post_input_data,
        ),
        expected_code=201,
        expected_json={
            **post_input_data,
            "id": int,
        },
    ).json()["id"]

    async with active_session():
        post = await Post.find_first_by_id(post_id)
        assert post is not None
        await post.delete()


@pytest.mark.parametrize(
    "kind",
    [
        pytest.param(ChannelType.TASKS, id="tasks"),
        pytest.param(ChannelType.CHAT, id="chat"),
        pytest.param(ChannelType.CALL, id="call"),
        pytest.param(ChannelType.BOARD, id="board"),
    ],
)
async def test_post_creation_invalid_channel_kind(
    mub_client: TestClient,
    active_session: ActiveSession,
    channel: Channel,
    kind: ChannelType,
) -> None:
    await change_channel_kind(active_session, channel.id, kind)

    post_input_data = PostInputFactory.build_json()
    assert_response(
        mub_client.post(
            f"/mub/community-service/channels/{channel.id}/posts/",
            json=post_input_data,
        ),
        expected_code=409,
        expected_json={"detail": "Invalid channel kind"},
    )


async def test_post_retrieving(
    mub_client: TestClient,
    post: Post,
    post_data: AnyJSON,
) -> None:
    assert_response(
        mub_client.get(f"/mub/community-service/posts/{post.id}/"),
        expected_json=post_data,
    )


async def test_post_updating(
    mub_client: TestClient,
    post: Post,
    post_data: AnyJSON,
) -> None:
    post_patch_data = PostPatchFactory.build_json()

    assert_response(
        mub_client.patch(
            f"/mub/community-service/posts/{post.id}/",
            json=post_patch_data,
        ),
        expected_json={**post_data, **post_patch_data},
    )


async def test_post_deleting(
    mub_client: TestClient,
    active_session: ActiveSession,
    post: Post,
) -> None:
    assert_nodata_response(
        mub_client.delete(f"/mub/community-service/posts/{post.id}/"),
    )

    async with active_session():
        assert (await Post.find_first_by_id(post.id)) is None


@pytest.mark.parametrize(
    ("method", "body_factory"),
    [
        pytest.param("GET", None, id="get"),
        pytest.param("PATCH", PostPatchFactory, id="patch"),
        pytest.param("DELETE", None, id="delete"),
    ],
)
async def test_post_not_finding(
    mub_client: TestClient,
    deleted_post_id: int,
    method: str,
    body_factory: type[BaseModelFactory[Any]] | None,
) -> None:
    assert_response(
        mub_client.request(
            method,
            f"/mub/community-service/posts/{deleted_post_id}/",
            json=body_factory and body_factory.build_json(),
        ),
        expected_code=404,
        expected_json={"detail": "Post not found"},
    )
