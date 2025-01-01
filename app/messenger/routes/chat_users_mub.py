from typing import Annotated

from fastapi import Path

from app.common.fastapi_ext import APIRouterExt
from app.messenger.dependencies.chat_users_dep import ChatUserByIds
from app.messenger.dependencies.chats_dep import ChatById
from app.messenger.models.chat_users_db import ChatUser

router = APIRouterExt(tags=["chat-users mub"])


@router.post(
    "/chats/{chat_id}/users/{user_id}/",
    status_code=201,
    response_model=ChatUser.ResponseSchema,
    summary="Create chat-user for any user in any chat",
)
async def create_chat_user(
    chat: ChatById,
    user_id: Annotated[int, Path()],
    data: ChatUser.InputSchema,
) -> ChatUser:
    return await ChatUser.create(chat_id=chat.id, user_id=user_id, **data.model_dump())


@router.get(
    "/chats/{chat_id}/users/{user_id}/",
    response_model=ChatUser.ResponseSchema,
    summary="Retrieve chat-user data for any user in any chat",
)
async def retrieve_chat_user(chat_user: ChatUserByIds) -> ChatUser:
    return chat_user


@router.patch(
    "/chats/{chat_id}/users/{user_id}/",
    response_model=ChatUser.ResponseSchema,
    summary="Update chat-user data for any user in any chat",
)
async def patch_chat_user(
    chat_user: ChatUserByIds,
    data: ChatUser.PatchSchema,
) -> ChatUser:
    chat_user.update(**data.model_dump(exclude_defaults=True))
    return chat_user


@router.delete(
    "/chats/{chat_id}/users/{user_id}/",
    status_code=204,
    summary="Delete chat-user data for any user in any chat",
)
async def delete_chat_user(chat_user: ChatUserByIds) -> None:
    await chat_user.delete()
