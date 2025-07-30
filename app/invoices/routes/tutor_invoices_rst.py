from collections.abc import Sequence

from starlette import status

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt, Responses
from app.invoices.dependencies.recipient_invoices_dep import TutorRecipientInvoiceById
from app.invoices.models.recipient_invoices_db import (
    PaymentStatus,
    RecipientInvoice,
    TutorInvoiceSearchSchema,
)

router = APIRouterExt(tags=["tutor invoices"])


@router.post(
    path="/roles/tutor/recipient-invoices/searches/",
    response_model=list[RecipientInvoice.TutorResponseSchema],
    summary="List paginated recipient invoices created by the current user",
)
async def list_recipient_invoices(
    auth_data: AuthorizationData,
    search: TutorInvoiceSearchSchema,
) -> Sequence[RecipientInvoice]:
    return await RecipientInvoice.find_paginated_by_tutor(
        tutor_id=auth_data.user_id,
        **search.model_dump(),
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


class PaymentStatusResponses(Responses):
    INVALID_CONFIRM = status.HTTP_409_CONFLICT, "Payment already confirmed"


@router.post(
    path="/roles/tutor/recipient-invoices/{recipient_invoice_id}/payment-confirmation/",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=PaymentStatusResponses.responses(),
    summary="Confirm payment status of the recipient invoice by tutor",
)
async def update_recipient_invoice_payment_status(
    recipient_invoice: TutorRecipientInvoiceById,
) -> None:
    if recipient_invoice.status == PaymentStatus.COMPLETE:
        raise PaymentStatusResponses.INVALID_CONFIRM
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
