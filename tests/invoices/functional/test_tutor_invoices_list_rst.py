from collections.abc import AsyncIterator
from datetime import datetime
from decimal import Decimal
from typing import Any

import pytest
from starlette.testclient import TestClient

from app.invoices.models.invoices_db import Invoice
from app.invoices.models.recipient_invoices_db import PaymentStatus, RecipientInvoice
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_response
from tests.common.types import AnyJSON
from tests.common.utils import remove_none_values
from tests.invoices import factories

pytestmark = pytest.mark.anyio

TUTOR_INVOICE_LIST_SIZE = 5


@pytest.fixture()
async def recipient_invoices_data(
    active_session: ActiveSession,
    tutor_id: int,
    student_id: int,
    total: Decimal,
) -> AsyncIterator[list[tuple[RecipientInvoice, AnyJSON]]]:
    recipient_invoices: list[RecipientInvoice] = []

    async with active_session():
        for _ in range(TUTOR_INVOICE_LIST_SIZE):
            invoice: Invoice = await Invoice.create(
                **factories.InvoiceInputFactory.build_python(),
                tutor_id=tutor_id,
            )
            recipient_invoice = await RecipientInvoice.create(
                invoice=invoice,
                student_id=student_id,
                total=total,
                status=PaymentStatus.WF_PAYMENT,
            )
            recipient_invoices.insert(0, recipient_invoice)

    yield [
        (
            recipient_invoice,
            RecipientInvoice.TutorResponseSchema.model_validate(
                recipient_invoice
            ).model_dump(mode="json"),
        )
        for recipient_invoice in recipient_invoices
    ]

    async with active_session():
        for recipient_invoice in recipient_invoices:
            await recipient_invoice.invoice.delete()


@pytest.mark.parametrize(
    ("index_after", "limit"),
    [
        pytest.param(None, TUTOR_INVOICE_LIST_SIZE, id="start_to_end"),
        pytest.param(
            TUTOR_INVOICE_LIST_SIZE // 2,
            TUTOR_INVOICE_LIST_SIZE // 2,
            id="middle_to_end",
        ),
        pytest.param(None, TUTOR_INVOICE_LIST_SIZE // 2, id="start_to_middle"),
    ],
)
async def test_tutor_invoices_listing(
    tutor_client: TestClient,
    recipient_invoices_data: list[tuple[RecipientInvoice, AnyJSON]],
    index_after: int | None,
    limit: int,
) -> None:
    after_created_at: datetime = (
        recipient_invoices_data[-1][0].created_at
        if index_after is None
        else recipient_invoices_data[index_after][0].created_at
    )
    after_recipient_invoice_id: int = (
        recipient_invoices_data[-1][0].id
        if index_after is None
        else recipient_invoices_data[index_after][0].id
    )
    after: dict[str, Any] | None = (
        None
        if index_after is None
        else {
            "created_at": after_created_at.isoformat(),
            "recipient_invoice_id": after_recipient_invoice_id,
        }
    )

    filtered_recipient_invoices_data = [
        (recipient_invoice, recipient_invoice_data)
        for (recipient_invoice, recipient_invoice_data) in recipient_invoices_data
        if index_after is None
        or recipient_invoice.created_at < after_created_at
        or (
            recipient_invoice.created_at == after_created_at
            and recipient_invoice.id > after_recipient_invoice_id
        )
    ]

    assert_response(
        tutor_client.post(
            "/api/protected/invoice-service/roles/tutor/recipient-invoices/searches/",
            json=remove_none_values(
                {
                    "after": after,
                    "limit": limit,
                }
            ),
        ),
        expected_json=[
            recipient_invoice_data
            for _, recipient_invoice_data in filtered_recipient_invoices_data[:limit]
        ],
    )
