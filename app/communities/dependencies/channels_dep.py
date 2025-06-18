from typing import Annotated

from fastapi import Depends, Path
from starlette import status

from app.common.fastapi_ext import Responses, with_responses
from app.communities.models.channels_db import Channel


class ChannelsResponses(Responses):
    CHANNEL_NOT_FOUND = status.HTTP_404_NOT_FOUND, "Channel not found"


@with_responses(ChannelsResponses)
async def get_channel_by_id(channel_id: Annotated[int, Path()]) -> Channel:
    channel = await Channel.find_first_by_id(channel_id)
    if channel is None:
        raise ChannelsResponses.CHANNEL_NOT_FOUND
    return channel


ChannelById = Annotated[Channel, Depends(get_channel_by_id)]
