from typing import Annotated

from fastapi import Depends, Path
from starlette import status

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import Responses, with_responses
from app.invoices.models.recipient_invoices_db import RecipientInvoice


class RecipientInvoiceResponses(Responses):
    RECIPIENT_INVOICE_NOT_FOUND = (
        status.HTTP_404_NOT_FOUND,
        "Recipient invoice not found",
    )


@with_responses(RecipientInvoiceResponses)
async def get_recipient_invoice(
    recipient_invoice_id: Annotated[int, Path()],
) -> RecipientInvoice:
    recipient_invoice = await RecipientInvoice.find_first_by_id(recipient_invoice_id)
    if recipient_invoice is None:
        raise RecipientInvoiceResponses.RECIPIENT_INVOICE_NOT_FOUND
    return recipient_invoice


RecipientInvoiceById = Annotated[RecipientInvoice, Depends(get_recipient_invoice)]


class AccessRecipientInvoiceResponses(Responses):
    ACCESS_DENIED = status.HTTP_403_FORBIDDEN, "Recipient invoice access denied"


@with_responses(AccessRecipientInvoiceResponses)
async def get_tutor_recipient_invoice(
    auth_data: AuthorizationData,
    recipient_invoice: RecipientInvoiceById,
) -> RecipientInvoice:
    if recipient_invoice.invoice.tutor_id != auth_data.user_id:
        raise AccessRecipientInvoiceResponses.ACCESS_DENIED
    return recipient_invoice


TutorRecipientInvoiceById = Annotated[
    RecipientInvoice, Depends(get_tutor_recipient_invoice)
]
