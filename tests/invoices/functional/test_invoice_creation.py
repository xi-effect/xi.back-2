import pytest
from freezegun import freeze_time
from pydantic_marshals.contains import assert_contains
from starlette import status
from starlette.testclient import TestClient

from app.common.utils.datetime import datetime_utc_now
from app.invoices.models.invoice_items_db import InvoiceItem
from app.invoices.models.invoices_db import Invoice
from app.invoices.models.recipient_invoices_db import PaymentStatus, RecipientInvoice
from app.invoices.routes.invoices_rst import InvoiceFormSchema
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_response
from tests.invoices import factories

pytestmark = pytest.mark.anyio


@freeze_time()
async def test_invoice_creation(
    active_session: ActiveSession,
    creator_client: TestClient,
    creator_user_id: int,
    recipient_user_id: int,
) -> None:
    invoice_data: Invoice.InputSchema = factories.InvoiceInputFactory.build()
    invoice_item_data: InvoiceItem.InputSchema = (
        factories.InvoiceItemInputFactory.build()
    )
    invoice_form_data = InvoiceFormSchema(
        invoice=invoice_data,
        items=[invoice_item_data],
        recipient_user_ids=[recipient_user_id],
    )

    invoice_id: int = assert_response(
        creator_client.post(
            "/api/protected/invoice-service/invoices/",
            json=invoice_form_data.model_dump(mode="json"),
        ),
        expected_code=status.HTTP_201_CREATED,
        expected_json={"id": int},
    ).json()["id"]

    async with active_session():
        invoice = await Invoice.find_first_by_id(invoice_id)
        assert invoice is not None
        assert_contains(
            invoice,
            {
                "creator_user_id": creator_user_id,
                "created_at": datetime_utc_now(),
                "total": invoice_item_data.price * invoice_item_data.quantity,
                **invoice_data.model_dump(),
            },
        )

        invoice_items = await InvoiceItem.find_all_by_kwargs(invoice_id=invoice_id)
        assert len(invoice_items) == 1
        assert_contains(
            invoice_items[0],
            {
                "position": 0,
                **invoice_item_data.model_dump(),
            },
        )

        recipient_invoices = await RecipientInvoice.find_all_by_kwargs(
            invoice_id=invoice_id
        )
        assert len(recipient_invoices) == 1
        assert_contains(
            recipient_invoices[0],
            {
                "recipient_user_id": recipient_user_id,
                "status": PaymentStatus.WF_PAYMENT,
            },
        )

        await invoice.delete()


async def test_invoice_creation_target_is_the_source(
    active_session: ActiveSession,
    creator_client: TestClient,
    creator_user_id: int,
) -> None:
    assert_response(
        creator_client.post(
            "/api/protected/invoice-service/invoices/",
            json=factories.InvoiceFormFactory.build_json(
                recipient_user_ids=[creator_user_id],
            ),
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={"detail": "Target is the source"},
    )
