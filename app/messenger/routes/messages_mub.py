from collections.abc import Sequence

from app.common.fastapi_ext import APIRouterExt
from app.common.utils.datetime import datetime_utc_now
from app.messenger.dependencies.chats_dep import ChatById
from app.messenger.dependencies.messages_dep import MessageById
from app.messenger.models.messages_db import Message

router = APIRouterExt(tags=["messages mub"])


@router.get(
    "/chats/{chat_id}/messages/",
    response_model=list[Message.ResponseSchema],
    summary="List paginated messages in a chat",
)
async def list_messages(
    chat: ChatById,
    offset: int,
    limit: int,
) -> Sequence[Message]:
    return await Message.find_paginated_by_chat_id(chat.id, offset, limit)


@router.post(
    "/chats/{chat_id}/messages/",
    status_code=201,
    response_model=Message.ResponseSchema,
    summary="Create a new message in a chat",
)
async def create_message(chat: ChatById, data: Message.InputMUBSchema) -> Message:
    return await Message.create(chat_id=chat.id, **data.model_dump())


@router.get(
    "/messages/{message_id}/",
    response_model=Message.ResponseSchema,
    summary="Retrieve any message by id",
)
async def retrieve_message(message: MessageById) -> Message:
    return message


@router.patch(
    "/messages/{message_id}/",
    response_model=Message.ResponseSchema,
    summary="Update any message by id",
)
async def patch_message(message: MessageById, data: Message.PatchSchema) -> Message:
    message.update(
        **data.model_dump(exclude_defaults=True),
        updated_at=datetime_utc_now(),
    )
    return message


@router.delete(
    "/messages/{message_id}/",
    status_code=204,
    summary="Delete any message by id",
)
async def delete_message(message: MessageById) -> None:
    await message.delete()
