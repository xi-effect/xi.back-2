from collections.abc import Sequence
from typing import Annotated

from pydantic import BaseModel, Field
from starlette import status

from app.common.config_bdg import classrooms_bridge, notifications_bridge
from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt, Responses
from app.common.schemas.notifications_sch import (
    NotificationInputSchema,
    NotificationKind,
    RecipientInvoiceNotificationPayloadSchema,
)
from app.invoices.dependencies.recipient_invoices_dep import (
    PaymentStatusResponses,
    TutorRecipientInvoiceByID,
)
from app.invoices.models.invoice_items_db import InvoiceItem
from app.invoices.models.invoices_db import Invoice
from app.invoices.models.recipient_invoices_db import (
    DetailedTutorRecipientInvoiceSchema,
    PaymentStatus,
    RecipientInvoice,
    TutorInvoiceSearchRequestSchema,
)

router = APIRouterExt(tags=["tutor invoices"])


@router.post(
    path="/roles/tutor/recipient-invoices/searches/",
    response_model=list[RecipientInvoice.TutorResponseSchema],
    summary="List paginated tutor recipient invoices for the current user",
)
async def list_tutor_recipient_invoices(
    auth_data: AuthorizationData,
    data: TutorInvoiceSearchRequestSchema,
) -> Sequence[RecipientInvoice]:
    return await RecipientInvoice.find_paginated_by_tutor_id(
        tutor_id=auth_data.user_id,
        search_params=data,
    )


@router.post(
    path="/roles/tutor/classrooms/{classroom_id}/recipient-invoices/searches/",
    response_model=list[RecipientInvoice.TutorResponseSchema],
    summary="List paginated tutor recipient invoices in a classroom by id",
)
async def list_tutor_classroom_recipient_invoices(
    auth_data: AuthorizationData,
    data: TutorInvoiceSearchRequestSchema,
    classroom_id: int,
) -> Sequence[RecipientInvoice]:
    return await RecipientInvoice.find_paginated_by_tutor_id(
        tutor_id=auth_data.user_id,
        search_params=data,
        classroom_id=classroom_id,
    )


class InvoiceFormSchema(BaseModel):
    invoice: Invoice.InputSchema
    items: Annotated[list[InvoiceItem.InputSchema], Field(min_length=1, max_length=10)]
    student_ids: Annotated[list[int] | None, Field(min_length=1, max_length=20)] = None


class InvoiceFormResponses(Responses):
    STUDENT_NOT_FOUND = status.HTTP_404_NOT_FOUND, "Student not found"


@router.post(
    path="/roles/tutor/classrooms/{classroom_id}/invoices/",
    status_code=status.HTTP_201_CREATED,
    response_model=Invoice.IDSchema,
    responses=InvoiceFormResponses.responses(),
    summary="Create a new invoice in a classroom by id",
)
async def create_invoice(
    data: InvoiceFormSchema,
    auth_data: AuthorizationData,
    classroom_id: int,
) -> Invoice:
    classroom_student_ids = await classrooms_bridge.list_classroom_student_ids(
        classroom_id=classroom_id
    )
    included_student_ids: list[int]
    if data.student_ids is None:
        included_student_ids = classroom_student_ids
    elif set(data.student_ids).issubset(set(classroom_student_ids)):
        included_student_ids = data.student_ids
    else:
        raise InvoiceFormResponses.STUDENT_NOT_FOUND

    total = sum(
        invoice_item_data.price * invoice_item_data.quantity
        for invoice_item_data in data.items
    )

    invoice = await Invoice.create(
        **data.invoice.model_dump(),
        tutor_id=auth_data.user_id,
        classroom_id=classroom_id,
    )

    for position, invoice_item_data in enumerate(data.items):
        await InvoiceItem.create(
            **invoice_item_data.model_dump(),
            invoice_id=invoice.id,
            position=position,
        )

    for student_id in included_student_ids:
        recipient_invoice = await RecipientInvoice.create(
            invoice_id=invoice.id,
            student_id=student_id,
            total=total,
            status=PaymentStatus.WF_SENDER_CONFIRMATION,
        )

        # TODO: batch sending or use invoice_ids instead
        await notifications_bridge.send_notification(
            NotificationInputSchema(
                payload=RecipientInvoiceNotificationPayloadSchema(
                    kind=NotificationKind.RECIPIENT_INVOICE_CREATED_V1,
                    recipient_invoice_id=recipient_invoice.id,
                ),
                recipient_user_ids=[student_id],
            )
        )

    return invoice


@router.get(
    path="/roles/tutor/recipient-invoices/{recipient_invoice_id}/",
    response_model=DetailedTutorRecipientInvoiceSchema.build_marshal(),
    summary="Retrieve tutor recipient invoice by id",
)
async def retrieve_tutor_recipient_invoice(
    recipient_invoice: TutorRecipientInvoiceByID,
) -> DetailedTutorRecipientInvoiceSchema:
    return DetailedTutorRecipientInvoiceSchema(
        invoice=recipient_invoice.invoice,
        recipient_invoice=recipient_invoice,
        invoice_items=await InvoiceItem.find_all_by_invoice_id(
            invoice_id=recipient_invoice.invoice_id
        ),
        student_id=recipient_invoice.student_id,
    )


@router.patch(
    path="/roles/tutor/recipient-invoices/{recipient_invoice_id}/",
    response_model=RecipientInvoice.TutorResponseSchema,
    summary="Update tutor recipient invoice by id",
)
async def patch_recipient_invoice(
    recipient_invoice: TutorRecipientInvoiceByID,
    patch_data: RecipientInvoice.PatchSchema,
) -> RecipientInvoice:
    recipient_invoice.update(**patch_data.model_dump(exclude_defaults=True))
    return recipient_invoice


@router.post(
    path="/roles/tutor/recipient-invoices/{recipient_invoice_id}/payment-confirmations/unilateral/",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=PaymentStatusResponses.responses(),
    summary="Unilaterally confirm tutor recipient invoice payment by id",
)
async def confirm_tutor_recipient_invoice_payment_with_payment_type(
    recipient_invoice: TutorRecipientInvoiceByID,
    data: RecipientInvoice.PaymentSchema,
) -> None:
    if recipient_invoice.status is not PaymentStatus.WF_SENDER_CONFIRMATION:
        raise PaymentStatusResponses.INVALID_CONFIRMATION
    recipient_invoice.update(**data.model_dump())
    recipient_invoice.status = PaymentStatus.COMPLETE


@router.post(
    path="/roles/tutor/recipient-invoices/{recipient_invoice_id}/payment-confirmations/receiver/",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=PaymentStatusResponses.responses(),
    summary="Confirm tutor recipient invoice payment by id",
)
async def confirm_tutor_recipient_invoice_payment(
    recipient_invoice: TutorRecipientInvoiceByID,
) -> None:
    if recipient_invoice.status is not PaymentStatus.WF_RECEIVER_CONFIRMATION:
        raise PaymentStatusResponses.INVALID_CONFIRMATION
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
