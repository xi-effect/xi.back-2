from typing import Annotated

from tmexio import PydanticPackager

from app.common.tmexio_ext import EventRouterExt
from app.communities.dependencies.board_channels_sio_dep import BoardChannelByIds
from app.communities.dependencies.communities_sio_dep import (
    current_participant_dependency,
)
from app.communities.models.board_channels_db import BoardChannel

router = EventRouterExt(tags=["board-channels"])


@router.on(
    "retrieve-board-channel",
    summary="Retrieve a board-channel by id",
    dependencies=[current_participant_dependency],
)
async def retrieve_board_channel(
    board_channel: BoardChannelByIds,
) -> Annotated[BoardChannel, PydanticPackager(BoardChannel.ResponseSchema)]:
    return board_channel
