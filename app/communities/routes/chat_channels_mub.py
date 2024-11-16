from app.common.fastapi_ext import APIRouterExt
from app.communities.dependencies.chat_channels_dep import ChatChannelById
from app.communities.models.chat_channels_db import ChatChannel

router = APIRouterExt(tags=["chat-channels mub"])


@router.get(
    "/channels/{channel_id}/chat/",
    response_model=ChatChannel.ResponseSchema,
    summary="Retrieve a chat-channel by id",
)
async def retrieve_chat_channel(chat_channel: ChatChannelById) -> ChatChannel:
    return chat_channel
