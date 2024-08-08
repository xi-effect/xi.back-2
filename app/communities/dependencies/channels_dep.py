from typing import Annotated

from fastapi import Depends, Path

from app.common.fastapi_ext import Responses, with_responses
from app.communities.models.channels_db import Channel, ChannelType


class ChannelsResponses(Responses):
    CHANNEL_NOT_FOUND = 404, "Channel not found"


class ChannelsKindValidationResponses(Responses):
    INVALID_CHANNEL_KIND = 409, "Invalid channel kind"


@with_responses(ChannelsResponses)
async def get_channel_by_id(channel_id: Annotated[int, Path()]) -> Channel:
    channel = await Channel.find_first_by_id(channel_id)
    if channel is None:
        raise ChannelsResponses.CHANNEL_NOT_FOUND
    return channel


ChannelByIdDependency = Depends(get_channel_by_id)
ChannelById = Annotated[Channel, ChannelByIdDependency]


@with_responses(ChannelsKindValidationResponses)
async def get_posts_channel_by_id(channel: ChannelById) -> Channel:
    if channel.kind is not ChannelType.POSTS:
        raise ChannelsKindValidationResponses.INVALID_CHANNEL_KIND
    return channel


PostsChannelById = Annotated[Channel, Depends(get_posts_channel_by_id)]
