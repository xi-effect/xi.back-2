from collections.abc import Sequence

from starlette import status

from app.common.fastapi_ext import APIRouterExt
from app.invoices.dependencies.invoices_dep import InvoiceById
from app.invoices.models.invoices_db import Invoice

router = APIRouterExt(tags=["invoices mub"])


@router.get(
    "/users/{creator_user_id}/invoices/",
    response_model=list[Invoice.ResponseSchema],
    summary="List invoices by user id",
)
async def get_list_invocies(
    creator_user_id: int,
    offset: int,
    limit: int,
) -> Sequence[Invoice]:
    return await Invoice.find_paginated_by_kwargs(
        creator_user_id=creator_user_id, offset=offset, limit=limit
    )


@router.patch(
    "/invoices/{invoice_id}/",
    response_model=Invoice.ResponseSchema,
    summary="Update invoice by id",
)
async def patch_invoice(invoice: InvoiceById, data: Invoice.PatchSchema) -> Invoice:
    invoice.update(**data.model_dump(exclude_defaults=True))
    return invoice


@router.delete(
    "/invoices/{invoice_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete inovice by id",
)
async def delete_invoice(invoice: InvoiceById) -> None:
    await invoice.delete()
