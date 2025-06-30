from typing import Annotated

from pydantic import BaseModel, Field
from starlette import status

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt, Responses
from app.invoices.models.invoice_items_db import InvoiceItem
from app.invoices.models.invoices_db import Invoice
from app.invoices.models.recipient_invoices_db import PaymentStatus, RecipientInvoice

router = APIRouterExt(tags=["invoices"])


class InvoiceFormSchema(BaseModel):
    invoice: Invoice.InputSchema
    items: Annotated[list[InvoiceItem.InputSchema], Field(min_length=1, max_length=10)]
    recipient_user_ids: Annotated[list[int], Field(min_length=1, max_length=20)]


class InvoiceFormResponses(Responses):
    TARGET_IS_THE_SOURCE = status.HTTP_409_CONFLICT, "Target is the source"


@router.post(
    path="/invoices/",
    status_code=status.HTTP_201_CREATED,
    response_model=Invoice.IDSchema,
    responses=InvoiceFormResponses.responses(),
    summary="Create a new invoice",
)
async def create_invoice(
    data: InvoiceFormSchema,
    auth_data: AuthorizationData,
) -> Invoice:
    if auth_data.user_id in data.recipient_user_ids:
        raise InvoiceFormResponses.TARGET_IS_THE_SOURCE
    # TODO check if creator is allowed to send invoices to recipients (51967762)

    total = sum(
        invoice_item_data.price * invoice_item_data.quantity
        for invoice_item_data in data.items
    )

    invoice = await Invoice.create(
        **data.invoice.model_dump(),
        creator_user_id=auth_data.user_id,
        total=total,
    )

    for position, invoice_item_data in enumerate(data.items):
        await InvoiceItem.create(
            **invoice_item_data.model_dump(),
            invoice_id=invoice.id,
            position=position,
        )

    for recipient_user_id in data.recipient_user_ids:
        await RecipientInvoice.create(
            invoice_id=invoice.id,
            recipient_user_id=recipient_user_id,
            status=PaymentStatus.WF_PAYMENT,
        )
        # TODO send notification to each recipient (worker task)

    return invoice
