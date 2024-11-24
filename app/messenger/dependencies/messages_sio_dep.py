from typing import Annotated
from uuid import UUID

from tmexio import EventException, register_dependency

from app.common.dependencies.authorization_sio_dep import AuthorizedUser
from app.messenger.dependencies.chats_sio_dep import ChatById
from app.messenger.models.messages_db import Message

message_not_found_exception = EventException(404, "Message not found")


@register_dependency(exceptions=[message_not_found_exception])
async def message_by_ids_dependency(message_id: UUID, chat: ChatById) -> Message:
    message = await Message.find_first_by_id(message_id)
    if message is None or message.chat_id != chat.id:
        raise message_not_found_exception
    return message


MessageByIds = Annotated[Message, message_by_ids_dependency]


not_your_message_exception = EventException(403, "Message is not yours")


@register_dependency(exceptions=[not_your_message_exception])
async def my_message_by_ids_dependency(
    user: AuthorizedUser, message: MessageByIds
) -> Message:
    if message.sender_user_id != user.user_id:
        raise not_your_message_exception
    return message


MyMessageByIds = Annotated[Message, my_message_by_ids_dependency]
