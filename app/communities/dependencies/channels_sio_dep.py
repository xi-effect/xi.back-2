from typing import Annotated

from tmexio import EventException, register_dependency

from app.communities.dependencies.communities_sio_dep import CommunityById
from app.communities.models.channels_db import Channel

channel_not_found = EventException(404, "Channel not found")


@register_dependency(exceptions=[channel_not_found])
async def get_channel_by_ids(
    channel_id: int,
    community: CommunityById,
) -> Channel:
    channel = await Channel.find_first_by_id(channel_id)
    if channel is None or channel.community_id != community.id:
        raise channel_not_found
    return channel


ChannelByIds = Annotated[Channel, get_channel_by_ids]
