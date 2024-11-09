from collections.abc import Sequence
from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field
from tmexio import AsyncSocket, Emitter, PydanticPackager

from app.common.dependencies.authorization_sio_dep import AuthorizedUser
from app.common.sqlalchemy_ext import db
from app.common.tmexio_ext import EventRouterExt
from app.common.utils.datetime import datetime_utc_now
from app.messenger.dependencies.chats_sio_dep import ChatById
from app.messenger.dependencies.messages_sio_dep import MyMessageByIDs
from app.messenger.models.messages_db import Message
from app.messenger.rooms import chat_room

router = EventRouterExt(tags=["chat-messages"])


@router.on(
    "list-latest-chat-messages",
    summary="Open the chat & list the latest messages",
    # TODO dependencies=[allowed_reading_dependency],
)
async def list_latest_messages(
    chat: ChatById,
    limit: Annotated[int, Field(gt=0, le=100)],
    socket: AsyncSocket,
) -> Annotated[Sequence[Message], PydanticPackager(list[Message.ResponseSchema])]:
    await socket.enter_room(chat_room(chat.id))
    return await Message.find_by_chat_id_created_before(
        chat_id=chat.id, created_before=None, limit=limit
    )


@router.on(
    "list-chat-messages",
    summary="List older messages in the chat",
    # TODO dependencies=[allowed_reading_dependency],
)
async def list_messages(
    chat: ChatById,
    created_before: datetime,
    limit: Annotated[int, Field(gt=0, le=100)],
) -> Annotated[Sequence[Message], PydanticPackager(list[Message.ResponseSchema])]:
    return await Message.find_by_chat_id_created_before(
        chat_id=chat.id, created_before=created_before, limit=limit
    )


@router.on(
    "close-chat",
    summary="Close a chat",
)  # TODO no session here
async def close_chat(chat_id: int, socket: AsyncSocket) -> None:
    await socket.leave_room(chat_room(chat_id))


@router.on(
    "send-chat-message",
    summary="Send a new message in the chat",
    server_summary="A new message has been sent in the current chat",
    # TODO dependencies=[allowed_sending_dependency],
)
async def send_message(
    user: AuthorizedUser,
    chat: ChatById,
    data: Message.InputSchema,
    duplex_emitter: Annotated[Emitter[Message], Message.ServerEventSchema],
) -> Annotated[Message, PydanticPackager(Message.ResponseSchema, code=201)]:
    message = await Message.create(
        chat_id=chat.id,
        sender_user_id=user.user_id,
        **data.model_dump(),
    )
    await db.session.commit()

    await duplex_emitter.emit(
        message,
        target=chat_room(chat.id),
        exclude_self=True,
    )
    return message


UpdateMessageEmitter = Annotated[
    Emitter[Message],
    router.register_server_emitter(
        Message.ServerEventSchema,
        event_name="edit-chat-message",
        summary="Message has been updated in the current chat",
    ),
]


@router.on(
    "edit-my-chat-message",
    summary="Update any message from current user by id",
    # TODO dependencies=[allowed_reading_dependency],
)
async def update_message(
    message: MyMessageByIDs,
    data: Message.PatchSchema,
    update_message_emitter: UpdateMessageEmitter,
) -> Annotated[Message, PydanticPackager(Message.ResponseSchema)]:
    message.update(
        **data.model_dump(exclude_defaults=True),
        updated_at=datetime_utc_now(),
    )
    await db.session.commit()

    await update_message_emitter.emit(
        message,
        target=chat_room(message.chat_id),
        exclude_self=True,
    )
    return message


class MessageIDsSchema(BaseModel):
    chat_id: int
    message_id: UUID


DeleteMessageEmitter = Annotated[
    Emitter[MessageIDsSchema],
    router.register_server_emitter(
        MessageIDsSchema,
        event_name="delete-chat-message",
        summary="A user has left or has been kicked from the current community",
    ),
]


@router.on(
    "delete-my-chat-message",
    summary="Delete any message from current user by id",
    # TODO dependencies=[allowed_reading_dependency],
)
async def delete_message(
    message: MyMessageByIDs,
    delete_message_emitter: DeleteMessageEmitter,
) -> None:
    await message.delete()
    await db.session.commit()

    await delete_message_emitter.emit(
        MessageIDsSchema(chat_id=message.chat_id, message_id=message.id),
        target=chat_room(message.chat_id),
        exclude_self=True,
    )
