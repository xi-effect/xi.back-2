from typing import Annotated
from uuid import UUID

from fastapi import Body, Depends, Path
from starlette import status

from app.common.fastapi_ext import Responses, with_responses
from app.storage_v2.dependencies.storage_token_dep import (
    StorageTokenPayload,
    StorageTokenResponses,
)
from app.storage_v2.models.access_groups_db import AccessGroup
from app.storage_v2.models.ydocs_db import YDoc

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


@with_responses(StorageTokenResponses)
async def get_my_ydoc_by_id(
    ydoc: YDocByID,
    storage_token_payload: StorageTokenPayload,
) -> YDoc:
    access_group = await AccessGroup.find_first_by_id(
        storage_token_payload.access_group_id
    )
    if access_group is None:
        raise StorageTokenResponses.INVALID_STORAGE_TOKEN
    if access_group.main_ydoc_id != ydoc.id:
        raise StorageTokenResponses.INVALID_STORAGE_TOKEN
    return ydoc


MyYDocByID = Annotated[YDoc, Depends(get_my_ydoc_by_id)]
