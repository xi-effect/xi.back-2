import pytest
from starlette.testclient import TestClient

from app.posts.models.post_channels_db import PostChannel
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.types import AnyJSON

pytestmark = pytest.mark.anyio


async def test_post_channel_creation(
    active_session: ActiveSession,
    internal_client: TestClient,
    post_channel_data: AnyJSON,
    deleted_post_channel_id: int,
) -> None:
    assert_nodata_response(
        internal_client.post(
            f"/internal/post-service/post-channels/{deleted_post_channel_id}/",
            json=post_channel_data,
        ),
        expected_code=201,
    )

    async with active_session():
        post_channel = await PostChannel.find_first_by_id(deleted_post_channel_id)
        assert post_channel is not None
        await post_channel.delete()


async def test_post_channel_creation_post_channel_already_exists(
    internal_client: TestClient,
    post_channel_data: AnyJSON,
    post_channel: PostChannel,
) -> None:
    assert_response(
        internal_client.post(
            f"/internal/post-service/post-channels/{post_channel.id}/",
            json=post_channel_data,
        ),
        expected_code=409,
        expected_json={"detail": "Post-channel already exists"},
    )


async def test_post_channel_deleting(
    active_session: ActiveSession,
    internal_client: TestClient,
    post_channel: PostChannel,
) -> None:
    assert_nodata_response(
        internal_client.delete(
            f"/internal/post-service/post-channels/{post_channel.id}/",
        ),
    )

    async with active_session():
        assert await PostChannel.find_first_by_id(post_channel.id) is None


async def test_post_channel_deleting_post_channel_not_found(
    internal_client: TestClient, deleted_post_channel_id: int
) -> None:
    assert_response(
        internal_client.delete(
            f"/internal/post-service/post-channels/{deleted_post_channel_id}/",
        ),
        expected_code=404,
        expected_json={"detail": "Post-channel not found"},
    )
