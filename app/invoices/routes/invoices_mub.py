from collections.abc import Sequence

from app.common.fastapi_ext import APIRouterExt
from app.invoices.models.invoices_db import Invoice

router = APIRouterExt(tags=["invoice-service mub"])


@router.get(
    "/users/{creator_user_id}/invoices", response_model=list[Invoice.ResponseSchema]
)
async def get_user_invocies(
    creator_user_id: int,
    offset: int,
    limit: int,
) -> Sequence[Invoice]:
    return await Invoice.find_paginated_by_kwargs(
        creator_user_id=creator_user_id, offset=offset, limit=limit
    )


# @router.patch("/invoices/{id}")
# async def updateInvoiceComment(id: int, comment: str):
#     return await {}


# @router.delete("/invoices/{id}")
# async def deleteInvoice(id: int):
#     return await {}
