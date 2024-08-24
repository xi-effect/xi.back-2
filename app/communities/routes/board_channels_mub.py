from fastapi import Response

from app.common.fastapi_ext import APIRouterExt
from app.communities.dependencies.board_channels_dep import (
    BoardChannelById,
    BoardChannelContent,
)

router = APIRouterExt(tags=["board-channels mub"])


@router.get(
    "/channels/{channel_id}/board/content/",
    summary="Retrieve board-channel content",
)
async def retrieve_board_channel_content(board_channel: BoardChannelById) -> Response:
    return Response(
        content=board_channel.content, media_type="application/octet-stream"
    )


@router.put(
    "/channels/{channel_id}/board/content/",
    status_code=204,
    summary="Update board-channel content",
)
async def update_board_channel_content(
    board_channel: BoardChannelById, content: BoardChannelContent
) -> None:
    board_channel.update(content=content)
