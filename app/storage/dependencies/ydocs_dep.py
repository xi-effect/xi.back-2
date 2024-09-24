from typing import Annotated
from uuid import UUID

from fastapi import Body, Depends, Path

from app.common.fastapi_ext import Responses, with_responses
from app.storage.models.ydocs_db import YDoc


class YDocResponses(Responses):
    YDOC_NOT_FOUND = 404, "YDoc not found"


@with_responses(YDocResponses)
async def get_ydoc_by_id(ydoc_id: Annotated[UUID, Path()]) -> YDoc:
    ydoc = await YDoc.find_first_by_id(ydoc_id)
    if ydoc is None:
        raise YDocResponses.YDOC_NOT_FOUND
    return ydoc


YDocByIdDependency = Depends(get_ydoc_by_id)
YDocById = Annotated[YDoc, YDocByIdDependency]

YDocContent = Annotated[bytes, Body(..., media_type="application/octet-stream")]
