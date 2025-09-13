from typing import Annotated

from fastapi import Depends, Path
from starlette import status

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import Responses, with_responses
from app.invoices.models.invoice_item_templates_db import InvoiceItemTemplate


class InvoiceItemTemplateResponses(Responses):
    INVOICE_ITEM_TEMPLATE_NOT_FOUND = (
        status.HTTP_404_NOT_FOUND,
        "Invoice item template not found",
    )


@with_responses(InvoiceItemTemplateResponses)
async def get_invoice_item_template_by_id(
    invoice_item_template_id: Annotated[int, Path()],
) -> InvoiceItemTemplate:
    invoice_item_template = await InvoiceItemTemplate.find_first_by_id(
        invoice_item_template_id
    )
    if invoice_item_template is None:
        raise InvoiceItemTemplateResponses.INVOICE_ITEM_TEMPLATE_NOT_FOUND
    return invoice_item_template


InvoiceItemTemplateByID = Annotated[
    InvoiceItemTemplate, Depends(get_invoice_item_template_by_id)
]


class MyTutorInvoiceItemTemplateResponses(Responses):
    ACCESS_DENIED = status.HTTP_403_FORBIDDEN, "Invoice item template access denied"


@with_responses(MyTutorInvoiceItemTemplateResponses)
async def get_my_tutor_invoice_item_template_by_id(
    invoice_item_template: InvoiceItemTemplateByID, auth_data: AuthorizationData
) -> InvoiceItemTemplate:
    if invoice_item_template.tutor_id != auth_data.user_id:
        raise MyTutorInvoiceItemTemplateResponses.ACCESS_DENIED
    return invoice_item_template


MyTutorInvoiceItemTemplateByID = Annotated[
    InvoiceItemTemplate, Depends(get_my_tutor_invoice_item_template_by_id)
]
