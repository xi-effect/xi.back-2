from collections.abc import Sequence
from typing import Annotated

from fastapi import Query
from starlette import status

from app.common.fastapi_ext import APIRouterExt
from app.invoices.dependencies.invoices_dep import InvoiceById
from app.invoices.models.invoices_db import Invoice

router = APIRouterExt(tags=["invoices mub"])


@router.get(
    "/users/{tutor_id}/invoices/",
    response_model=list[Invoice.ResponseSchema],
    summary="List invoices by user id",
)
async def list_invoices(
    tutor_id: int,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> Sequence[Invoice]:
    return await Invoice.find_paginated_by_kwargs(
        tutor_id=tutor_id, offset=offset, limit=limit
    )


@router.patch(
    "/invoices/{invoice_id}/",
    response_model=Invoice.ResponseSchema,
    summary="Update invoice by id",
)
async def patch_invoice(invoice: InvoiceById, data: Invoice.PatchMUBSchema) -> Invoice:
    invoice.update(**data.model_dump(exclude_defaults=True))
    return invoice


@router.delete(
    "/invoices/{invoice_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete invoice by id",
)
async def delete_invoice(invoice: InvoiceById) -> None:
    await invoice.delete()
