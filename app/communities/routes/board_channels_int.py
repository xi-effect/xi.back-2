from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt
from app.common.schemas.storage_sch import YDocAccessLevel
from app.communities.dependencies.board_channels_dep import BoardChannelById
from app.communities.services import access_svc

router = APIRouterExt(tags=["board-channels internal"])


@router.get(
    "/channels/{channel_id}/board/access-level/",
    summary="Retrieve user's access level to board-channel",
)
async def retrieve_board_channel_access_level(
    board_channel: BoardChannelById,
    auth_data: AuthorizationData,
) -> YDocAccessLevel:
    return await access_svc.retrieve_community_access_level(
        community_id=board_channel.channel.community_id, user_id=auth_data.user_id
    )
