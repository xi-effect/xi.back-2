from typing import Annotated

from fastapi import Depends, Path

from app.common.fastapi_ext import Responses, with_responses
from app.messenger.models.message_drafts_db import MessageDraft


class MessageDraftResponses(Responses):
    MESSAGE_DRAFT_NOT_FOUND = 404, "Message draft not found"


@with_responses(MessageDraftResponses)
async def get_message_draft_by_ids(
    chat_id: Annotated[int, Path()], user_id: Annotated[int, Path()]
) -> MessageDraft:
    message_draft = await MessageDraft.find_first_by_kwargs(
        chat_id=chat_id, user_id=user_id
    )
    if message_draft is None:
        raise MessageDraftResponses.MESSAGE_DRAFT_NOT_FOUND
    return message_draft


MessageDraftByIds = Annotated[MessageDraft, Depends(get_message_draft_by_ids)]
