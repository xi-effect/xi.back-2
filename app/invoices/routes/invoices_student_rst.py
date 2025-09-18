from collections.abc import Sequence

from starlette import status

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt
from app.invoices.dependencies.recipient_invoices_dep import (
    PaymentStatusResponses,
    StudentRecipientInvoiceByID,
)
from app.invoices.models.invoice_items_db import InvoiceItem
from app.invoices.models.recipient_invoices_db import (
    DetailedStudentRecipientInvoiceSchema,
    PaymentStatus,
    RecipientInvoice,
    StudentInvoiceSearchRequestSchema,
)

router = APIRouterExt(tags=["student invoices"])


@router.post(
    path="/roles/student/recipient-invoices/searches/",
    response_model=list[RecipientInvoice.StudentResponseSchema],
    summary="List paginated student recipient invoices for the current user",
)
async def list_student_recipient_invoices(
    auth_data: AuthorizationData,
    data: StudentInvoiceSearchRequestSchema,
) -> Sequence[RecipientInvoice]:
    return await RecipientInvoice.find_paginated_by_student_id(
        student_id=auth_data.user_id, cursor=data.cursor, limit=data.limit
    )


@router.get(
    path="/roles/student/recipient-invoices/{recipient_invoice_id}/",
    response_model=DetailedStudentRecipientInvoiceSchema.build_marshal(),
    summary="Retrieve student recipient invoice by id",
)
async def retrieve_student_recipient_invoice(
    recipient_invoice: StudentRecipientInvoiceByID,
) -> DetailedStudentRecipientInvoiceSchema:
    return DetailedStudentRecipientInvoiceSchema(
        invoice=recipient_invoice.invoice,
        recipient_invoice=recipient_invoice,
        invoice_items=await InvoiceItem.find_all_by_invoice_id(
            invoice_id=recipient_invoice.invoice_id
        ),
        tutor_id=recipient_invoice.tutor_id,
    )


@router.post(
    path="/roles/student/recipient-invoices/{recipient_invoice_id}/payment-confirmations/sender/",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=PaymentStatusResponses.responses(),
    summary="Confirm student recipient invoice payment by id",
)
async def confirm_student_recipient_invoice_payment_with_payment_type(
    recipient_invoice: StudentRecipientInvoiceByID,
    data: RecipientInvoice.PaymentSchema,
) -> None:
    if recipient_invoice.status is not PaymentStatus.WF_SENDER_CONFIRMATION:
        raise PaymentStatusResponses.INVALID_CONFIRMATION
    recipient_invoice.update(**data.model_dump())
    recipient_invoice.status = PaymentStatus.WF_RECEIVER_CONFIRMATION
