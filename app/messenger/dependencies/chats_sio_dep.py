from typing import Annotated

from tmexio import EventException, register_dependency

from app.messenger.models.chats_db import Chat

chat_not_found = EventException(404, "Chat not found")


@register_dependency(exceptions=[chat_not_found])
async def chat_by_channel_id_dependency(channel_id: int) -> Chat:
    chat = await Chat.find_first_by_kwargs(channel_id=channel_id)
    if chat is None:
        raise chat_not_found
    return chat


ChatByChannelId = Annotated[Chat, chat_by_channel_id_dependency]
