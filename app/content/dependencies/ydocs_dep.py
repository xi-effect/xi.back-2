from typing import Annotated
from uuid import UUID

from fastapi import Body, Depends, Path
from starlette import status

from app.common.fastapi_ext import Responses, with_responses
from app.content.dependencies.content_token_dep import (
    ContentTokenPayload,
    ContentTokenResponses,
)
from app.content.models.ydocs_db import YDoc

YDocContent = Annotated[bytes, Body(..., media_type="application/octet-stream")]


class YDocResponses(Responses):
    YDOC_NOT_FOUND = status.HTTP_404_NOT_FOUND, "YDoc not found"


@with_responses(YDocResponses)
async def get_ydoc_by_id(ydoc_id: Annotated[UUID, Path()]) -> YDoc:
    ydoc = await YDoc.find_first_by_id(ydoc_id)
    if ydoc is None:
        raise YDocResponses.YDOC_NOT_FOUND
    return ydoc


YDocByID = Annotated[YDoc, Depends(get_ydoc_by_id)]


@with_responses(ContentTokenResponses)
async def get_my_ydoc_by_id(
    ydoc: YDocByID,
    content_token_payload: ContentTokenPayload,
) -> YDoc:
    if content_token_payload.ydoc_id != ydoc.id:
        raise ContentTokenResponses.INVALID_CONTENT_TOKEN
    return ydoc


MyYDocByID = Annotated[YDoc, Depends(get_my_ydoc_by_id)]


@with_responses(YDocResponses)
async def get_ydoc_by_content_token(
    content_token_payload: ContentTokenPayload,
) -> YDoc:
    ydoc = await YDoc.find_first_by_id(content_token_payload.ydoc_id)
    if ydoc is None:
        raise YDocResponses.YDOC_NOT_FOUND
    return ydoc


ContentTokenYDoc = Annotated[YDoc, Depends(get_ydoc_by_content_token)]
