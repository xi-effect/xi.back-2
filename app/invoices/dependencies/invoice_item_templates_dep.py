from typing import Annotated

from fastapi import Depends, Path
from starlette import status

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import Responses, with_responses
from app.invoices.models.invoice_item_templates_db import InvoiceItemTemplate


class InvoiceItemTemplateResponses(Responses):
    ACCESS_DENIED = status.HTTP_403_FORBIDDEN, "Invoice item template access denied"
    INVOICE_ITEM_TEMPLATE_NOT_FOUND = (
        status.HTTP_404_NOT_FOUND,
        "Invoice item template not found",
    )


@with_responses(InvoiceItemTemplateResponses)
async def get_invoice_item_template_by_id(
    invoice_item_template_id: Annotated[int, Path()], auth_data: AuthorizationData
) -> InvoiceItemTemplate:
    invoice_item_template = await InvoiceItemTemplate.find_first_by_id(
        invoice_item_template_id
    )
    if invoice_item_template is None:
        raise InvoiceItemTemplateResponses.INVOICE_ITEM_TEMPLATE_NOT_FOUND
    if invoice_item_template.creator_user_id != auth_data.user_id:
        raise InvoiceItemTemplateResponses.ACCESS_DENIED
    return invoice_item_template


InvoiceItemTemplateByID = Annotated[
    InvoiceItemTemplate, Depends(get_invoice_item_template_by_id)
]
