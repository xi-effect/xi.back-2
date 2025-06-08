from typing import Annotated

from fastapi import Path
from starlette import status

from app.common.fastapi_ext import APIRouterExt
from app.messenger.dependencies.chats_dep import ChatById
from app.messenger.dependencies.message_drafts_dep import MessageDraftByIds
from app.messenger.models.message_drafts_db import MessageDraft

router = APIRouterExt(tags=["message drafts mub"])


@router.post(
    path="/chats/{chat_id}/users/{user_id}/draft/",
    status_code=status.HTTP_201_CREATED,
    response_model=MessageDraft.ResponseSchema,
    summary="Create message draft for any user in any chat",
)
async def create_message_draft(
    chat: ChatById,
    user_id: Annotated[int, Path()],
    data: MessageDraft.InputSchema,
) -> MessageDraft:
    return await MessageDraft.create(
        chat_id=chat.id, user_id=user_id, **data.model_dump()
    )


@router.patch(
    path="/chats/{chat_id}/users/{user_id}/draft/",
    response_model=MessageDraft.ResponseSchema,
    summary="Update message draft for any user in any chat",
)
async def update_message_draft(
    message_draft: MessageDraftByIds, data: MessageDraft.PatchSchema
) -> MessageDraft:
    message_draft.update(**data.model_dump(exclude_defaults=True))
    return message_draft


@router.get(
    path="/chats/{chat_id}/users/{user_id}/draft/",
    response_model=MessageDraft.ResponseSchema,
    summary="Retrieve message draft for any user in any chat",
)
async def get_message_draft(message_draft: MessageDraftByIds) -> MessageDraft:
    return message_draft


@router.delete(
    path="/chats/{chat_id}/users/{user_id}/draft/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete message draft for any user in any chat",
)
async def delete_message_draft(message_draft: MessageDraftByIds) -> None:
    await message_draft.delete()
