from collections.abc import Sequence

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt
from app.invoices.dependencies.recipient_invoices_dep import StudentRecipientInvoiceByID
from app.invoices.models.invoice_items_db import InvoiceItem
from app.invoices.models.recipient_invoices_db import (
    DetailedStudentInvoiceSchema,
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
    return await RecipientInvoice.find_paginated_by_student(
        student_id=auth_data.user_id, cursor=data.cursor, limit=data.limit
    )


@router.get(
    path="/roles/student/recipient-invoices/{recipient_invoice_id}/",
    response_model=DetailedStudentInvoiceSchema,
    summary="Retrieve student recipient invoice by id",
)
async def retrieve_student_recipient_invoice(
    recipient_invoice: StudentRecipientInvoiceByID,
) -> DetailedStudentInvoiceSchema:
    return DetailedStudentInvoiceSchema(
        invoice=recipient_invoice.invoice,
        items=await InvoiceItem.find_all_by_kwargs(
            InvoiceItem.position, invoice_id=recipient_invoice.invoice_id
        ),
        tutor_id=recipient_invoice.tutor_id,
    )
