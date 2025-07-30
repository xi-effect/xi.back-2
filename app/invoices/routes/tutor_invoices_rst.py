from collections.abc import Sequence

from starlette import status

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt
from app.invoices.dependencies.recipient_invoices_dep import TutorRecipientInvoiceById
from app.invoices.models.invoices_db import Invoice
from app.invoices.models.recipient_invoices_db import PaymentStatus, RecipientInvoice

router = APIRouterExt(tags=["tutor invoices"])


@router.get(
    path="/roles/tutor/recipient-invoices/",
    response_model=list[RecipientInvoice.TutorResponseSchema],
    summary="List paginated recipient invoices created by the current tutor",
)
async def list_recipient_invoices(
    auth_data: AuthorizationData, offset: int = 0, limit: int = 12
) -> Sequence[RecipientInvoice]:
    return await RecipientInvoice.find_paginated_by_criteria(
        offset,
        limit,
        RecipientInvoice.invoice.has(Invoice.tutor_id == auth_data.user_id),
        order_by_one=Invoice.created_at.desc(),
    )


@router.patch(
    path="/roles/tutor/recipient-invoices/{recipient_invoice_id}/",
    response_model=RecipientInvoice.TutorResponseSchema,
    summary="Update recipient invoice by id",
)
async def patch_recipient_invoice(
    tutor_invoice: TutorRecipientInvoiceById,
    patch_data: RecipientInvoice.PatchSchema,
) -> RecipientInvoice:
    tutor_invoice.update(**patch_data.model_dump(exclude_defaults=True))
    return tutor_invoice


@router.patch(
    path="/roles/tutor/recipient-invoices/{recipient_invoice_id}/status/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Update payment status of recipient invoice by id for tutor(Confirm payment by tutor)",
)
async def update_recipient_invoice_payment_status(
    recipient_invoice: TutorRecipientInvoiceById,
) -> None:
    recipient_invoice.status = PaymentStatus.COMPLETE


@router.delete(
    path="/roles/tutor/recipient-invoices/{recipient_invoice_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete recipient invoice by id",
)
async def delete_recipient_invoice(
    recipient_invoice: TutorRecipientInvoiceById,
) -> None:
    await recipient_invoice.delete()
