from collections.abc import Sequence
from datetime import datetime
from typing import Annotated

from pydantic import Field
from pydantic_marshals.base import CompositeMarshalModel
from tmexio import AsyncSocket, PydanticPackager

from app.common.dependencies.authorization_sio_dep import AuthorizedUser
from app.common.sqlalchemy_ext import db
from app.common.tmexio_ext import EventRouterExt
from app.messenger.dependencies.chats_sio_dep import ChatById
from app.messenger.dependencies.messages_sio_dep import MessageByIds
from app.messenger.models.chat_users_db import ChatUser
from app.messenger.models.messages_db import Message
from app.messenger.rooms import chat_room

router = EventRouterExt(tags=["chats"])


class MyChatSchema(CompositeMarshalModel):
    # TODO message_draft
    latest_messages: list[Annotated[Message, Message.ResponseSchema]]
    last_message_read: datetime | None


@router.on(
    "open-chat",
    # TODO summary="Open the chat, retrieve message draft & list the latest messages",
    summary="Open the chat & list the latest messages",
    # TODO dependencies=[allowed_reading_dependency],
)
async def open_chat(
    *,
    user: AuthorizedUser,
    chat: ChatById,
    limit: Annotated[int, Field(gt=0, le=100)] = 50,
    socket: AsyncSocket,
) -> Annotated[MyChatSchema, PydanticPackager(MyChatSchema.build_marshal())]:
    await socket.enter_room(chat_room(chat.id))
    return MyChatSchema(
        latest_messages=await Message.find_by_chat_id_created_before(
            chat_id=chat.id, created_before=None, limit=limit
        ),
        last_message_read=(
            await ChatUser.find_or_create(chat_id=chat.id, user_id=user.user_id)
        ).last_message_read,
    )


@router.on(
    "list-chat-messages",
    summary="List older messages in the chat",
    # TODO dependencies=[allowed_reading_dependency],
)
async def list_messages(
    chat: ChatById,
    created_before: datetime,
    limit: Annotated[int, Field(gt=0, le=100)] = 50,
) -> Annotated[Sequence[Message], PydanticPackager(list[Message.ResponseSchema])]:
    return await Message.find_by_chat_id_created_before(
        chat_id=chat.id, created_before=created_before, limit=limit
    )


@router.on(
    "list-chat-pinned-messages",
    summary="List pinned messages in the chat",
    # TODO dependencies=[allowed_reading_dependency],
)
async def list_pinned_messages(
    chat: ChatById,
    created_before: datetime | None = None,
    limit: Annotated[int, Field(gt=0, le=100)] = 50,
) -> Annotated[Sequence[Message], PydanticPackager(list[Message.ResponseSchema])]:
    return await Message.find_by_chat_id_created_before(
        chat_id=chat.id, created_before=created_before, limit=limit, only_pinned=True
    )


@router.on(
    "read-chat-message",
    summary="Mark any message by id and all messages before it as read",
    # TODO dependencies=[allowed_reading_dependency],
)
async def mark_message_as_read(
    user: AuthorizedUser,
    message: MessageByIds,
) -> None:
    chat_user = await ChatUser.find_or_create(
        chat_id=message.chat_id, user_id=user.user_id
    )
    if (
        chat_user.last_message_read is not None
        and message.created_at <= chat_user.last_message_read
    ):
        return
    chat_user.last_message_read = message.created_at
    await db.session.commit()


@router.on(
    "close-chat",
    summary="Close a chat",
)  # TODO no session here
async def close_chat(chat_id: int, socket: AsyncSocket) -> None:
    await socket.leave_room(chat_room(chat_id))
