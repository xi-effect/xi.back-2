from collections.abc import Sequence
from typing import Annotated

from pydantic import BaseModel, Field
from starlette import status

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt, Responses
from app.invoices.dependencies.recipient_invoices_dep import TutorRecipientInvoiceByID
from app.invoices.models.invoice_items_db import InvoiceItem
from app.invoices.models.invoices_db import Invoice
from app.invoices.models.recipient_invoices_db import (
    DetailedTutorInvoiceSchema,
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
    return await RecipientInvoice.find_paginated_by_tutor(
        tutor_id=auth_data.user_id, cursor=data.cursor, limit=data.limit
    )


class InvoiceFormSchema(BaseModel):
    invoice: Invoice.InputSchema
    items: Annotated[list[InvoiceItem.InputSchema], Field(min_length=1, max_length=10)]
    student_ids: Annotated[list[int], Field(min_length=1, max_length=20)]


class InvoiceFormResponses(Responses):
    TARGET_IS_THE_SOURCE = status.HTTP_409_CONFLICT, "Target is the source"


@router.post(
    path="/roles/tutor/invoices/",
    status_code=status.HTTP_201_CREATED,
    response_model=Invoice.IDSchema,
    responses=InvoiceFormResponses.responses(),
    summary="Create a new invoice",
)
async def create_invoice(
    data: InvoiceFormSchema,
    auth_data: AuthorizationData,
) -> Invoice:
    if auth_data.user_id in data.student_ids:
        raise InvoiceFormResponses.TARGET_IS_THE_SOURCE
    # TODO check if creator is allowed to send invoices to recipients (51967762)

    total = sum(
        invoice_item_data.price * invoice_item_data.quantity
        for invoice_item_data in data.items
    )

    invoice = await Invoice.create(
        **data.invoice.model_dump(),
        tutor_id=auth_data.user_id,
    )

    for position, invoice_item_data in enumerate(data.items):
        await InvoiceItem.create(
            **invoice_item_data.model_dump(),
            invoice_id=invoice.id,
            position=position,
        )

    for student_id in data.student_ids:
        await RecipientInvoice.create(
            invoice_id=invoice.id,
            student_id=student_id,
            total=total,
            status=PaymentStatus.WF_PAYMENT,
        )
        # TODO send notification to each recipient (worker task)

    return invoice


@router.get(
    path="/roles/tutor/recipient-invoices/{recipient_invoice_id}/",
    response_model=DetailedTutorInvoiceSchema,
    summary="Retrieve tutor recipient invoice by id",
)
async def retrieve_tutor_recipient_invoice(
    recipient_invoice: TutorRecipientInvoiceByID,
) -> DetailedTutorInvoiceSchema:
    return DetailedTutorInvoiceSchema(
        invoice=recipient_invoice.invoice,
        items=await InvoiceItem.find_all_by_kwargs(
            InvoiceItem.position, invoice_id=recipient_invoice.invoice_id
        ),
        student_id=recipient_invoice.student_id,
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


@router.delete(
    path="/roles/tutor/recipient-invoices/{recipient_invoice_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete tutor recipient invoice by id",
)
async def delete_recipient_invoice(
    recipient_invoice: TutorRecipientInvoiceByID,
) -> None:
    await recipient_invoice.delete()
