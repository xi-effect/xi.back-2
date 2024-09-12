from typing import Annotated
from uuid import UUID

from fastapi import Body, Depends, Path

from app.common.fastapi_ext import Responses, with_responses
from app.storage.models.hokus_db import Hoku


class HokuResponses(Responses):
    HOKU_NOT_FOUND = 404, "Hoku not found"


@with_responses(HokuResponses)
async def get_hoku_by_id(hoku_id: Annotated[UUID, Path()]) -> Hoku:
    hoku = await Hoku.find_first_by_id(hoku_id)
    if hoku is None:
        raise HokuResponses.HOKU_NOT_FOUND
    return hoku


HokuByIdDependency = Depends(get_hoku_by_id)
HokuById = Annotated[Hoku, HokuByIdDependency]

HokuContent = Annotated[bytes, Body(..., media_type="application/octet-stream")]
