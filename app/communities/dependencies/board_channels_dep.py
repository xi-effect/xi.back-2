from typing import Annotated

from fastapi import Depends, Path

from app.common.fastapi_ext import Responses, with_responses
from app.communities.models.board_channels_db import BoardChannel


class BoardChannelResponses(Responses):
    BOARD_CHANNEL_NOT_FOUND = 404, "Board-channel not found"


@with_responses(BoardChannelResponses)
async def get_board_channel_by_id(channel_id: Annotated[int, Path()]) -> BoardChannel:
    board_channel = await BoardChannel.find_first_by_id(channel_id)
    if board_channel is None:
        raise BoardChannelResponses.BOARD_CHANNEL_NOT_FOUND
    return board_channel


BoardChannelById = Annotated[BoardChannel, Depends(get_board_channel_by_id)]
