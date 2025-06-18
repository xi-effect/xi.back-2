from starlette import status

from app.common.fastapi_ext import APIRouterExt
from app.messenger.dependencies.chats_dep import ChatById
from app.messenger.models.chats_db import Chat

router = APIRouterExt(tags=["chats internal"])


@router.post(
    "/chats/",
    status_code=status.HTTP_201_CREATED,
    response_model=Chat.ResponseSchema,
    summary="Create a new chat",
)
async def create_chat(data: Chat.InputSchema) -> Chat:
    return await Chat.create(**data.model_dump())


@router.delete(
    "/chats/{chat_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete any chat by id",
)
async def delete_chat(chat: ChatById) -> None:
    # TODO may be make this asynchronous
    await chat.delete()
