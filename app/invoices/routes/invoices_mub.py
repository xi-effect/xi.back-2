from collections.abc import Sequence

from fastapi import HTTPException, status

from app.common.fastapi_ext import APIRouterExt
from app.invoices.dependencies.invoices_dep import InvoiceById
from app.invoices.models.invoices_db import Invoice
from app.users.models.users_db import User

router = APIRouterExt(tags=["invoice-service mub"])


@router.get(
    "/users/{creator_user_id}/invoices",
    response_model=list[Invoice.ResponseSchema],
    responses={
        status.HTTP_200_OK: {"description": "Invoices success founds"},
        status.HTTP_404_NOT_FOUND: {
            "description": "Invoices for this creator not found"
        },
    },
)
async def get_user_invocies(
    creator_user_id: int,
    offset: int,
    limit: int,
) -> Sequence[Invoice]:

    user = User.find_first_by_id(creator_user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {creator_user_id} not found",
        )

    return await Invoice.find_paginated_by_kwargs(
        creator_user_id=creator_user_id, offset=offset, limit=limit
    )


# @router.patch("/invoices/{id}")
# async def updateInvoiceComment(id: int, comment: str):
#     return await {}


@router.delete(
    "/invoices/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="delete any inovice by id",
)
async def delete_invoice(invoice: InvoiceById) -> None:
    return await invoice.delete()
