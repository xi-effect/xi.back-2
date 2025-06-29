from collections.abc import Sequence

from starlette import status

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt
from app.common.responses import LimitedListResponses
from app.common.utils.datetime import datetime_utc_now
from app.invoices.dependencies.invoice_item_templates_dep import InvoiceItemTemplateByID
from app.invoices.models.invoice_item_templates_db import InvoiceItemTemplate

router = APIRouterExt(tags=["invoice item templates"])


@router.get(
    path="/invoice-item-templates/",
    response_model=list[InvoiceItemTemplate.ResponseSchema],
    summary="List all invoice item templates for the current user",
)
async def list_invoice_item_templates(
    auth_data: AuthorizationData,
) -> Sequence[InvoiceItemTemplate]:
    return await InvoiceItemTemplate.find_all_by_creator(
        creator_user_id=auth_data.user_id
    )


@router.post(
    path="/invoice-item-templates/",
    status_code=status.HTTP_201_CREATED,
    response_model=InvoiceItemTemplate.ResponseSchema,
    responses=LimitedListResponses.responses(),
    summary="Create a new invoice item template for the current user",
)
async def create_invoice_item_template(
    input_data: InvoiceItemTemplate.InputSchema,
    auth_data: AuthorizationData,
) -> InvoiceItemTemplate:
    if await InvoiceItemTemplate.is_limit_per_user_reached(user_id=auth_data.user_id):
        raise LimitedListResponses.QUANTITY_EXCEEDED
    return await InvoiceItemTemplate.create(
        **input_data.model_dump(),
        creator_user_id=auth_data.user_id,
    )


@router.get(
    path="/invoice-item-templates/{invoice_item_template_id}/",
    response_model=InvoiceItemTemplate.ResponseSchema,
    summary="Retrieve invoice item template by id",
)
async def retrieve_invoice_item_template(
    invoice_item_template: InvoiceItemTemplateByID,
) -> InvoiceItemTemplate:
    return invoice_item_template


@router.patch(
    path="/invoice-item-templates/{invoice_item_template_id}/",
    response_model=InvoiceItemTemplate.ResponseSchema,
    summary="Update invoice item template by id",
)
async def patch_invoice_item_template(
    invoice_item_template: InvoiceItemTemplateByID,
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
    invoice_item_template: InvoiceItemTemplateByID,
) -> None:
    await invoice_item_template.delete()
