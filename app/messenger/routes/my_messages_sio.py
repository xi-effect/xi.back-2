from typing import Annotated

from tmexio import Emitter, PydanticPackager

from app.common.dependencies.authorization_sio_dep import AuthorizedUser
from app.common.sqlalchemy_ext import db
from app.common.tmexio_ext import EventRouterExt
from app.common.utils.datetime import datetime_utc_now
from app.messenger.dependencies.chats_sio_dep import ChatById
from app.messenger.dependencies.messages_sio_dep import MyMessageByIds
from app.messenger.models.messages_db import Message, MessageIdsSchema
from app.messenger.rooms import chat_room

router = EventRouterExt(tags=["my-messages"])


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


@router.on(
    "edit-chat-message-content",
    summary="Update content of a message by id sent by the current user",
    server_summary="Content of a message in the current chat has been edited",
    # TODO dependencies=[allowed_reading_dependency],
)
async def edit_message_content(
    message: MyMessageByIds,
    data: Message.InputSchema,
    duplex_emitter: Annotated[Emitter[Message], Message.ServerEventSchema],
) -> Annotated[Message, PydanticPackager(Message.ResponseSchema)]:
    message.update(
        **data.model_dump(),
        updated_at=datetime_utc_now(),
    )
    await db.session.commit()

    await duplex_emitter.emit(
        message,
        target=chat_room(message.chat_id),
        exclude_self=True,
    )
    return message


DeleteMessageEmitter = Annotated[
    Emitter[MessageIdsSchema],
    router.register_server_emitter(
        MessageIdsSchema,
        event_name="delete-chat-message",
        summary="Message has been deleted in the current chat",
    ),
]


@router.on(
    "delete-my-chat-message",
    summary="Delete any message from current user by id",
    # TODO dependencies=[allowed_reading_dependency],
)
async def delete_message(
    message: MyMessageByIds,
    delete_message_emitter: DeleteMessageEmitter,
) -> None:
    await message.delete()
    await db.session.commit()

    await delete_message_emitter.emit(
        MessageIdsSchema(chat_id=message.chat_id, message_id=message.id),
        target=chat_room(message.chat_id),
        exclude_self=True,
    )
