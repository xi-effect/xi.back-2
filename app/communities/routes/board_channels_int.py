from fastapi import Response
from pydantic import BaseModel

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt, Responses
from app.communities.dependencies.board_channels_dep import (
    BoardChannelById,
    BoardChannelContent,
)
from app.communities.dependencies.channels_dep import ChannelById
from app.communities.models.participants_db import Participant

router = APIRouterExt(tags=["board-channels internal"])


class ParticipantResponses(Responses):
    NO_COMMUNITY_ACCESS = (403, "No access to community")


class AccessLevelSchema(BaseModel):
    write_access: bool


@router.get(
    "/channels/{channel_id}/board/access-level/",
    responses=ParticipantResponses.responses(),
    summary="Retrieve user's access level to board-channel",
)
async def retrieve_board_channel_access_level(
    _board_channel: BoardChannelById,
    channel: ChannelById,
    auth_data: AuthorizationData,
) -> AccessLevelSchema:
    participant = await Participant.find_first_by_kwargs(
        community_id=channel.community_id, user_id=auth_data.user_id
    )
    if participant is None:
        raise ParticipantResponses.NO_COMMUNITY_ACCESS
    return AccessLevelSchema(write_access=participant.is_owner)


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
