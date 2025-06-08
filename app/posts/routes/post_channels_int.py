from starlette import status

from app.common.fastapi_ext import APIRouterExt, Responses
from app.posts.dependencies.post_channels_dep import PostChannelById
from app.posts.models.post_channels_db import PostChannel

router = APIRouterExt(tags=["post-channels internal"])


class PostChannelExistenceResponses(Responses):
    POST_CHANNEL_ALREADY_EXISTS = (
        status.HTTP_409_CONFLICT,
        "Post-channel already exists",
    )


@router.post(
    "/post-channels/{channel_id}/",
    status_code=status.HTTP_201_CREATED,
    responses=PostChannelExistenceResponses.responses(),
    summary="Create a new post-channel",
)
async def create_post_channel(channel_id: int, data: PostChannel.InputSchema) -> None:
    if (await PostChannel.find_first_by_id(channel_id)) is not None:
        raise PostChannelExistenceResponses.POST_CHANNEL_ALREADY_EXISTS
    await PostChannel.create(id=channel_id, **data.model_dump())


@router.delete(
    "/post-channels/{channel_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete any post-channel by id",
)
async def delete_post_channel(post_channel: PostChannelById) -> None:
    # TODO may be make this asynchronous
    await post_channel.delete()
