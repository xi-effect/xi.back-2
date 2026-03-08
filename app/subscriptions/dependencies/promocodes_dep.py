from typing import Annotated

from fastapi import Depends, Path
from starlette import status

from app.common.fastapi_ext import Responses, with_responses
from app.subscriptions.models.promocodes_db import Promocode


class PromocodeResponses(Responses):
    PROMOCODE_NOT_FOUND = status.HTTP_404_NOT_FOUND, "Promocode not found"


@with_responses(PromocodeResponses)
async def get_promocode_by_id(
    promocode_id: Annotated[int, Path()],
) -> Promocode:
    promocode = await Promocode.find_first_by_id(promocode_id)
    if promocode is None:
        raise PromocodeResponses.PROMOCODE_NOT_FOUND
    return promocode


PromocodeByID = Annotated[Promocode, Depends(get_promocode_by_id)]


@with_responses(PromocodeResponses)
async def get_promocode_by_code(
    code: Annotated[str, Path()],
) -> Promocode:
    promocode = await Promocode.find_first_by_kwargs(code=code)
    if promocode is None:
        raise PromocodeResponses.PROMOCODE_NOT_FOUND
    return promocode


PromocodeByCode = Annotated[Promocode, Depends(get_promocode_by_code)]
