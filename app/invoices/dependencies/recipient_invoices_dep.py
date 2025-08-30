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
async def get_recipient_invoice_by_id(
    recipient_invoice_id: Annotated[int, Path()],
) -> RecipientInvoice:
    recipient_invoice = await RecipientInvoice.find_first_by_id(recipient_invoice_id)
    if recipient_invoice is None:
        raise RecipientInvoiceResponses.RECIPIENT_INVOICE_NOT_FOUND
    return recipient_invoice


RecipientInvoiceByID = Annotated[RecipientInvoice, Depends(get_recipient_invoice_by_id)]


class MyTutorRecipientInvoiceResponses(Responses):
    TUTOR_ACCESS_DENIED = (
        status.HTTP_403_FORBIDDEN,
        "Recipient invoice tutor access denied",
    )


@with_responses(MyTutorRecipientInvoiceResponses)
async def get_my_tutor_recipient_invoice_by_id(
    auth_data: AuthorizationData,
    recipient_invoice: RecipientInvoiceByID,
) -> RecipientInvoice:
    if recipient_invoice.invoice.tutor_id != auth_data.user_id:
        raise MyTutorRecipientInvoiceResponses.TUTOR_ACCESS_DENIED
    return recipient_invoice


TutorRecipientInvoiceByID = Annotated[
    RecipientInvoice, Depends(get_my_tutor_recipient_invoice_by_id)
]


class MyStudentRecipientInvoiceResponses(Responses):
    STUDENT_ACCESS_DENIED = (
        status.HTTP_403_FORBIDDEN,
        "Recipient invoice student access denied",
    )


@with_responses(MyStudentRecipientInvoiceResponses)
async def get_my_student_recipient_invoice_by_id(
    auth_data: AuthorizationData,
    recipient_invoice: RecipientInvoiceByID,
) -> RecipientInvoice:
    if recipient_invoice.student_id != auth_data.user_id:
        raise MyStudentRecipientInvoiceResponses.STUDENT_ACCESS_DENIED
    return recipient_invoice


StudentRecipientInvoiceByID = Annotated[
    RecipientInvoice, Depends(get_my_student_recipient_invoice_by_id)
]


class PaymentStatusResponses(Responses):
    INVALID_CONFIRMATION = (
        status.HTTP_409_CONFLICT,
        "Invalid payment confirmation for the current payment status",
    )
