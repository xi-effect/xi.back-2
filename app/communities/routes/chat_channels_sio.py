from typing import Annotated

from tmexio import PydanticPackager

from app.common.tmexio_ext import EventRouterExt
from app.communities.dependencies.chat_channels_sio_dep import ChatChannelByIds
from app.communities.dependencies.communities_sio_dep import (
    current_participant_dependency,
)
from app.communities.models.chat_channels_db import ChatChannel

router = EventRouterExt(tags=["chat-channels"])


@router.on(
    "retrieve-chat-channel",
    summary="Retrieve a chat-channel by id",
    dependencies=[current_participant_dependency],
)
async def retrieve_chat_channel(
    chat_channel: ChatChannelByIds,
) -> Annotated[ChatChannel, PydanticPackager(ChatChannel.ResponseSchema)]:
    return chat_channel
