from collections.abc import Sequence

from starlette import status

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt, Responses
from app.invoices.dependencies.recipient_invoices_dep import TutorRecipientInvoiceByID
from app.invoices.models.recipient_invoices_db import (
    PaymentStatus,
    RecipientInvoice,
    TutorInvoiceSearchRequestSchema,
)

router = APIRouterExt(tags=["tutor recipient invoices"])


@router.post(
    path="/roles/tutor/recipient-invoices/searches/",
    response_model=list[RecipientInvoice.TutorResponseSchema],
    summary="List paginated tutor recipient invoices for the current user",
)
async def list_recipient_invoices(
    auth_data: AuthorizationData,
    data: TutorInvoiceSearchRequestSchema,
) -> Sequence[RecipientInvoice]:
    return await RecipientInvoice.find_paginated_by_tutor(
        tutor_id=auth_data.user_id, cursor=data.cursor, limit=data.limit
    )


@router.patch(
    path="/roles/tutor/recipient-invoices/{recipient_invoice_id}/",
    response_model=RecipientInvoice.TutorResponseSchema,
    summary="Update recipient invoice by id",
)
async def patch_recipient_invoice(
    tutor_invoice: TutorRecipientInvoiceByID,
    patch_data: RecipientInvoice.PatchSchema,
) -> RecipientInvoice:
    tutor_invoice.update(**patch_data.model_dump(exclude_defaults=True))
    return tutor_invoice


class PaymentStatusResponses(Responses):
    ALREADY_CONFIRMED = status.HTTP_409_CONFLICT, "Payment already confirmed"


@router.post(
    path="/roles/tutor/recipient-invoices/{recipient_invoice_id}/payment-confirmation/",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=PaymentStatusResponses.responses(),
    summary="Confirm tutor recipient invoice payment by id",
)
async def confirm_tutor_recipient_invoice_payment(
    recipient_invoice: TutorRecipientInvoiceByID,
) -> None:
    if recipient_invoice.status is PaymentStatus.COMPLETE:
        raise PaymentStatusResponses.ALREADY_CONFIRMED
    recipient_invoice.status = PaymentStatus.COMPLETE


@router.delete(
    path="/roles/tutor/recipient-invoices/{recipient_invoice_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete tutor recipient invoice by id",
)
async def delete_recipient_invoice(
    recipient_invoice: TutorRecipientInvoiceByID,
) -> None:
    await recipient_invoice.delete()
