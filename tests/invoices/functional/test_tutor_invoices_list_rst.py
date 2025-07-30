from collections.abc import AsyncIterator
from decimal import Decimal

import pytest
from starlette.testclient import TestClient

from app.invoices.models.invoices_db import Invoice
from app.invoices.models.recipient_invoices_db import PaymentStatus, RecipientInvoice
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_response
from tests.common.types import AnyJSON
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
            recipient_invoices.append(recipient_invoice)

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
    ("offset", "limit"),
    [
        pytest.param(0, TUTOR_INVOICE_LIST_SIZE, id="start_to_end"),
        pytest.param(
            TUTOR_INVOICE_LIST_SIZE // 2, TUTOR_INVOICE_LIST_SIZE, id="middle_to_end"
        ),
        pytest.param(0, TUTOR_INVOICE_LIST_SIZE // 2, id="start_to_middle"),
    ],
)
async def test_tutor_invoices_listing(
    tutor_client: TestClient,
    recipient_invoices_data: list[tuple[RecipientInvoice, AnyJSON]],
    offset: int,
    limit: int,
) -> None:
    assert_response(
        tutor_client.get(
            "/api/protected/invoice-service/roles/tutor/recipient-invoices/",
            params={"offset": offset, "limit": limit},
        ),
        expected_json=[
            recipient_invoice_data[1]
            for recipient_invoice_data in recipient_invoices_data[
                offset : offset + limit
            ]
        ],
    )
