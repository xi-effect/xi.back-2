from app.common.fastapi_ext import APIRouterExt
from app.communities.dependencies.board_channels_dep import BoardChannelById
from app.communities.models.board_channels_db import BoardChannel

router = APIRouterExt(tags=["board-channels mub"])


@router.get(
    "/channels/{channel_id}/board/",
    response_model=BoardChannel.ResponseSchema,
    summary="Retrieve a board-channel by id",
)
async def retrieve_board_channel(board_channel: BoardChannelById) -> BoardChannel:
    return board_channel
