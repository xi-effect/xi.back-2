from typing import Annotated

from fastapi import Depends, Path
from starlette import status

from app.common.fastapi_ext import Responses, with_responses
from app.communities.models.call_channels_db import CallChannel


class CallChannelResponses(Responses):
    CALL_CHANNEL_NOT_FOUND = status.HTTP_404_NOT_FOUND, "Call-channel not found"


@with_responses(CallChannelResponses)
async def get_call_channel_by_id(channel_id: Annotated[int, Path()]) -> CallChannel:
    call_channel = await CallChannel.find_first_by_id(channel_id)
    if call_channel is None:
        raise CallChannelResponses.CALL_CHANNEL_NOT_FOUND
    return call_channel


CallChannelById = Annotated[CallChannel, Depends(get_call_channel_by_id)]
