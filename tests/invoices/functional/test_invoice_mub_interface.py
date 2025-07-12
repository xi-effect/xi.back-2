import logging

import pytest
from starlette import status
from starlette.testclient import TestClient

from app.invoices.models.invoices_db import Invoice
from app.invoices.routes.invoices_rst import InvoiceFormSchema
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_response
from tests.invoices.factories import InvoiceInputFactory, InvoiceItemInputFactory

logger = logging.getLogger(__name__)


pytestmark = pytest.mark.anyio

INVOICES_LIST = 5


async def test_invoices_listing(
    active_session: ActiveSession,
    mub_client: TestClient,
    creator_user_id: int,
    recipient_user_id: int,
) -> None:
    logger.info("invoivce gen")
    invoices_data: list[Invoice.InputSchema] = [
        InvoiceInputFactory.build() for _ in range(INVOICES_LIST)
    ]
    invoices_item_data = InvoiceItemInputFactory.build()
    total = invoices_item_data.price * invoices_item_data.quantity
    invoices_schema = [
        InvoiceFormSchema(
            invoice=invoice,
            items=[invoices_item_data],
            recipient_user_ids=[recipient_user_id],
        )
        for invoice in invoices_data
    ]

    async with active_session():
        invoices = [
            await Invoice.create(
                **invoice_schema.invoice.model_dump(),
                creator_user_id=creator_user_id,
                total=total,
            )
            for invoice_schema in invoices_schema
        ]

    assert_response(
        mub_client.get(
            f"/mub/invoice-service/users/{creator_user_id}/invoices",
        ),
        expected_code=status.HTTP_200_OK,
        expected_json=[
            Invoice.InputSchema(**invoices[i].__dict__).model_dump(mode="json")
            for i in range(len(invoices))
        ],
    )

    async with active_session():
        for invoice in invoices:
            await invoice.delete()
