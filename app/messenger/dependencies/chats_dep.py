from typing import Annotated

from fastapi import Depends, Path
from starlette import status

from app.common.fastapi_ext import Responses, with_responses
from app.messenger.models.chats_db import Chat


class ChatResponses(Responses):
    CHAT_NOT_FOUND = status.HTTP_404_NOT_FOUND, "Chat not found"


@with_responses(ChatResponses)
async def get_chat_by_id(chat_id: Annotated[int, Path()]) -> Chat:
    chat = await Chat.find_first_by_id(chat_id)
    if chat is None:
        raise ChatResponses.CHAT_NOT_FOUND
    return chat


ChatById = Annotated[Chat, Depends(get_chat_by_id)]
