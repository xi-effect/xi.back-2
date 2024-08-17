import pytest

from app.posts.models.post_channels_db import PostChannel
from app.posts.models.posts_db import Post
from tests.common.active_session import ActiveSession
from tests.common.types import AnyJSON
from tests.posts import factories


@pytest.fixture()
async def post_channel_data() -> AnyJSON:
    return factories.PostChannelInputFactory.build_json()


@pytest.fixture()
async def post_channel(
    active_session: ActiveSession,
    post_channel_data: AnyJSON,
) -> PostChannel:
    async with active_session():
        return await PostChannel.create(**post_channel_data)


@pytest.fixture()
async def deleted_post_channel_id(
    active_session: ActiveSession,
    post_channel: PostChannel,
) -> int:
    async with active_session():
        await post_channel.delete()
    return post_channel.id


@pytest.fixture()
async def post(
    active_session: ActiveSession,
    post_channel: PostChannel,
) -> Post:
    async with active_session():
        return await Post.create(
            channel_id=post_channel.id,
            **factories.PostInputFactory.build_json(),
        )


@pytest.fixture()
def post_data(post: Post) -> AnyJSON:
    return Post.ResponseSchema.model_validate(post, from_attributes=True).model_dump(
        mode="json"
    )


@pytest.fixture()
async def deleted_post_id(
    active_session: ActiveSession,
    post: Post,
) -> int:
    async with active_session():
        await post.delete()
    return post.id
