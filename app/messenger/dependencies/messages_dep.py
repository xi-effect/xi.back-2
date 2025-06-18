from typing import Annotated
from uuid import UUID

from fastapi import Depends, Path
from starlette import status

from app.common.fastapi_ext import Responses, with_responses
from app.messenger.models.messages_db import Message


class MessageResponses(Responses):
    MESSAGE_NOT_FOUND = status.HTTP_404_NOT_FOUND, "Message not found"


@with_responses(MessageResponses)
async def get_message_by_id(message_id: Annotated[UUID, Path()]) -> Message:
    message = await Message.find_first_by_id(message_id)
    if message is None:
        raise MessageResponses.MESSAGE_NOT_FOUND
    return message


MessageById = Annotated[Message, Depends(get_message_by_id)]
