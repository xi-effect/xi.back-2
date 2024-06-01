from typing import Annotated

from fastapi import Depends, Path

from app.common.fastapi_ext import Responses, with_responses
from app.communities.models.channels_db import Channel


class ChannelsResponses(Responses):
    CHANNEL_NOT_FOUND = 404, "Channel not found"


@with_responses(ChannelsResponses)
async def get_channel_by_id(channel_id: Annotated[int, Path()]) -> Channel:
    channel = await Channel.find_first_by_id(channel_id)
    if channel is None:
        raise ChannelsResponses.CHANNEL_NOT_FOUND
    return channel


ChannelByIdDependency = Depends(get_channel_by_id)
ChannelById = Annotated[Channel, ChannelByIdDependency]
