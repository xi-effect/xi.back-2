from typing import Annotated

from tmexio import EventException, register_dependency

from app.communities.dependencies.communities_sio_dep import CommunityById
from app.communities.models.board_channels_db import BoardChannel

board_channel_not_found = EventException(404, "Board-channel not found")


@register_dependency(exceptions=[board_channel_not_found])
async def board_channel_by_ids_dependency(
    channel_id: int,
    community: CommunityById,
) -> BoardChannel:
    board_channel = await BoardChannel.find_first_by_id(channel_id)
    if board_channel is None or board_channel.channel.community_id != community.id:
        raise board_channel_not_found
    return board_channel


BoardChannelByIds = Annotated[BoardChannel, board_channel_by_ids_dependency]
