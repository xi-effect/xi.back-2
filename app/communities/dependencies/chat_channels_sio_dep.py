from typing import Annotated

from tmexio import EventException, register_dependency

from app.communities.dependencies.communities_sio_dep import CommunityById
from app.communities.models.chat_channels_db import ChatChannel

chat_channel_not_found = EventException(404, "Chat-channel not found")


@register_dependency(exceptions=[chat_channel_not_found])
async def chat_channel_by_ids_dependency(
    channel_id: int,
    community: CommunityById,
) -> ChatChannel:
    chat_channel = await ChatChannel.find_first_by_id(channel_id)
    if chat_channel is None or chat_channel.channel.community_id != community.id:
        raise chat_channel_not_found
    return chat_channel


ChatChannelByIds = Annotated[ChatChannel, chat_channel_by_ids_dependency]
