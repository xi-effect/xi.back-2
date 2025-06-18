from typing import Annotated

from fastapi import Depends, Path
from starlette import status

from app.common.fastapi_ext import Responses, with_responses
from app.posts.models.post_channels_db import PostChannel


class PostChannelResponses(Responses):
    POST_CHANNEL_NOT_FOUND = status.HTTP_404_NOT_FOUND, "Post-channel not found"


@with_responses(PostChannelResponses)
async def get_post_channel_by_id(channel_id: Annotated[int, Path()]) -> PostChannel:
    post_channel = await PostChannel.find_first_by_id(channel_id)
    if post_channel is None:
        raise PostChannelResponses.POST_CHANNEL_NOT_FOUND
    return post_channel


PostChannelById = Annotated[PostChannel, Depends(get_post_channel_by_id)]
