from typing import Annotated

from fastapi import Depends, Path

from app.common.fastapi_ext import Responses, with_responses
from app.communities.models.chat_channels_db import ChatChannel


class ChatChannelResponses(Responses):
    CHAT_CHANNEL_NOT_FOUND = 404, "Chat-channel not found"


@with_responses(ChatChannelResponses)
async def get_chat_channel_by_id(channel_id: Annotated[int, Path()]) -> ChatChannel:
    chat_channel = await ChatChannel.find_first_by_id(channel_id)
    if chat_channel is None:
        raise ChatChannelResponses.CHAT_CHANNEL_NOT_FOUND
    return chat_channel


ChatChannelById = Annotated[ChatChannel, Depends(get_chat_channel_by_id)]
