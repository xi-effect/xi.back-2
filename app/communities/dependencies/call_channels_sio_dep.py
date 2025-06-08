from typing import Annotated

from starlette import status
from tmexio import EventException, register_dependency

from app.communities.dependencies.communities_sio_dep import CommunityById
from app.communities.models.call_channels_db import CallChannel

call_channel_not_found = EventException(
    status.HTTP_404_NOT_FOUND, "Call-channel not found"
)


@register_dependency(exceptions=[call_channel_not_found])
async def call_channel_by_ids_dependency(
    channel_id: int,
    community: CommunityById,
) -> CallChannel:
    call_channel = await CallChannel.find_first_by_id(channel_id)
    if call_channel is None or call_channel.channel.community_id != community.id:
        raise call_channel_not_found
    return call_channel


CallChannelByIds = Annotated[CallChannel, call_channel_by_ids_dependency]
