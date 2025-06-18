from typing import Annotated

from fastapi import Depends, Path
from starlette import status

from app.common.fastapi_ext import Responses, with_responses
from app.messenger.models.chat_users_db import ChatUser


class ChatUserResponses(Responses):
    CHAT_USER_NOT_FOUND = status.HTTP_404_NOT_FOUND, "Chat-user not found"


@with_responses(ChatUserResponses)
async def get_chat_user_by_ids(
    chat_id: Annotated[int, Path()], user_id: Annotated[int, Path()]
) -> ChatUser:
    chat_user = await ChatUser.find_first_by_kwargs(chat_id=chat_id, user_id=user_id)
    if chat_user is None:
        raise ChatUserResponses.CHAT_USER_NOT_FOUND
    return chat_user


ChatUserByIds = Annotated[ChatUser, Depends(get_chat_user_by_ids)]
