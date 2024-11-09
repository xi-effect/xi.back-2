from typing import Annotated

from tmexio import EventException, register_dependency

from app.messenger.models.chats_db import Chat

chat_not_found = EventException(404, "Chat not found")


@register_dependency(exceptions=[chat_not_found])
async def chat_by_id_dependency(chat_id: int) -> Chat:
    chat = await Chat.find_first_by_id(chat_id)
    if chat is None:
        raise chat_not_found
    return chat


ChatById = Annotated[Chat, chat_by_id_dependency]
