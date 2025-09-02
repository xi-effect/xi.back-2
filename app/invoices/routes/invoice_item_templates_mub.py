from collections.abc import Sequence
from typing import Annotated

from fastapi import Body, Path
from starlette import status

from app.common.fastapi_ext import APIRouterExt
from app.common.responses import LimitedListResponses
from app.common.utils.datetime import datetime_utc_now
from app.invoices.dependencies.invoice_item_templates_dep import (
    InvoiceItemTemplateByIDMUB,
)
from app.invoices.models.invoice_item_templates_db import InvoiceItemTemplate

router = APIRouterExt(tags=["invoice item templates mub"])


@router.get(
    path="/users/{user_id}/invoice-item-templates/",
    response_model=list[InvoiceItemTemplate.ResponseSchema],
    summary="List all invoice item templates for the user",
)
async def list_invoice_item_templates(
    user_id: Annotated[int, Path()],
) -> Sequence[InvoiceItemTemplate]:
    return await InvoiceItemTemplate.find_all_by_tutor(tutor_id=user_id)


@router.get(
    path="/invoice-item-templates/{invoice_item_template_id}/",
    response_model=InvoiceItemTemplate.ResponseSchema,
    summary="Retrieve invoice item template by id",
)
async def retrieve_invoice_item_template(
    invoice_item_template_id: InvoiceItemTemplateByIDMUB,
) -> InvoiceItemTemplate:
    return invoice_item_template_id


@router.post(
    path="/users/{user_id}/invoice-item-templates/",
    status_code=status.HTTP_201_CREATED,
    response_model=InvoiceItemTemplate.ResponseSchema,
    responses=LimitedListResponses.responses(),
    summary="Create a new invoice item template for the current user",
)
async def create_invoice_item_template(
    user_id: Annotated[int, Path(...)],
    input_data: Annotated[InvoiceItemTemplate.InputSchema, Body()],
) -> InvoiceItemTemplate:
    if await InvoiceItemTemplate.is_limit_per_user_reached(user_id=user_id):
        raise LimitedListResponses.QUANTITY_EXCEEDED
    return await InvoiceItemTemplate.create(
        **input_data.model_dump(),
        creator_user_id=user_id,
    )


@router.patch(
    path="/invoice-item-templates/{invoice_item_template_id}/",
    response_model=InvoiceItemTemplate.ResponseSchema,
    summary="Update invoice item template by id",
)
async def patch_invoice_item_template(
    invoice_item_template: InvoiceItemTemplateByIDMUB,
    patch_data: InvoiceItemTemplate.PatchSchema,
) -> InvoiceItemTemplate:
    invoice_item_template.update(
        **patch_data.model_dump(exclude_defaults=True),
        updated_at=datetime_utc_now(),
    )
    return invoice_item_template


@router.delete(
    path="/invoice-item-templates/{invoice_item_template_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete invoice item template by id",
)
async def delete_invoice_item_template(
    invoice_item_template: InvoiceItemTemplateByIDMUB,
) -> None:
    await invoice_item_template.delete()
