from collections.abc import AsyncIterator
from decimal import Decimal

import pytest
from starlette.testclient import TestClient

from app.invoices.models.invoices_db import Invoice
from app.invoices.models.recipient_invoices_db import PaymentStatus, RecipientInvoice
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_response
from tests.common.utils import remove_none_values
from tests.invoices import factories

pytestmark = pytest.mark.anyio

TUTOR_INVOICE_LIST_SIZE = 5


@pytest.fixture()
async def recipient_invoices(
    active_session: ActiveSession,
    tutor_id: int,
    student_id: int,
    total: Decimal,
) -> AsyncIterator[list[RecipientInvoice]]:
    recipient_invoices: list[RecipientInvoice] = []

    async with active_session():
        for _ in range(TUTOR_INVOICE_LIST_SIZE):
            invoice: Invoice = await Invoice.create(
                **factories.InvoiceInputFactory.build_python(),
                tutor_id=tutor_id,
            )
            recipient_invoices.append(
                await RecipientInvoice.create(
                    invoice=invoice,
                    student_id=student_id,
                    total=total,
                    status=PaymentStatus.WF_PAYMENT,
                )
            )

    recipient_invoices.sort(
        key=lambda recipient_invoice: recipient_invoice.created_at, reverse=True
    )

    yield recipient_invoices

    async with active_session():
        for recipient_invoice in recipient_invoices:
            await recipient_invoice.invoice.delete()


@pytest.mark.parametrize(
    ("offset", "limit"),
    [
        pytest.param(0, TUTOR_INVOICE_LIST_SIZE, id="start_to_end"),
        pytest.param(
            TUTOR_INVOICE_LIST_SIZE // 2,
            TUTOR_INVOICE_LIST_SIZE,
            id="middle_to_end",
        ),
        pytest.param(0, TUTOR_INVOICE_LIST_SIZE // 2, id="start_to_middle"),
    ],
)
async def test_tutor_invoices_listing(
    tutor_client: TestClient,
    recipient_invoices: list[RecipientInvoice],
    offset: int,
    limit: int,
) -> None:
    assert_response(
        tutor_client.post(
            "/api/protected/invoice-service/roles/tutor/recipient-invoices/searches/",
            json=remove_none_values(
                {
                    "cursor": (
                        None
                        if offset == 0
                        else {
                            "created_at": recipient_invoices[
                                offset - 1
                            ].created_at.isoformat(),
                            "recipient_invoice_id": recipient_invoices[offset - 1].id,
                        }
                    ),
                    "limit": limit,
                }
            ),
        ),
        expected_json=[
            RecipientInvoice.TutorResponseSchema.model_validate(
                recipient_invoice, from_attributes=True
            )
            for recipient_invoice in recipient_invoices[offset:limit]
        ],
    )
