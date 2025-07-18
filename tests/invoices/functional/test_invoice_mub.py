import logging

import pytest
from starlette import status
from starlette.testclient import TestClient

from app.invoices.models.invoices_db import Invoice
from app.invoices.routes.invoices_rst import InvoiceFormSchema
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.invoices.factories import InvoiceInputFactory, InvoiceItemInputFactory

logger = logging.getLogger(__name__)


pytestmark = pytest.mark.anyio

INVOICES_LIST_SIZE = 5


@pytest.mark.parametrize(
    ("offset", "limit"),
    [
        pytest.param(0, INVOICES_LIST_SIZE, id="start_to_end"),
        pytest.param(INVOICES_LIST_SIZE // 2, INVOICES_LIST_SIZE, id="middle_to_end"),
        pytest.param(0, INVOICES_LIST_SIZE // 2, id="start_to_middle"),
    ],
)
async def test_invoices_listing(
    active_session: ActiveSession,
    mub_client: TestClient,
    offset: int,
    limit: int,
    creator_user_id: int,
    recipient_user_id: int,
) -> None:
    logger.info("invoivce gen")
    invoices_data: list[Invoice.InputSchema] = [
        InvoiceInputFactory.build() for _ in range(INVOICES_LIST_SIZE)
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
            params={"offset": offset, "limit": limit},
        ),
        expected_code=status.HTTP_200_OK,
        expected_json=[
            Invoice.ResponseSchema(**invoices[i].__dict__).model_dump(mode="json")
            for i in range(offset, limit)
        ],
    )

    async with active_session():
        for invoice in invoices:
            await invoice.delete()


async def test_invoice_empty_listing(
    active_session: ActiveSession,
    mub_client: TestClient,
    creator_user_id: int,
) -> None:

    assert_response(
        mub_client.get(
            f"/mub/invoice-service/users/{creator_user_id}/invoices",
            params={"offset": 0, "limit": 50},
        ),
        expected_code=status.HTTP_200_OK,
        expected_json=[],
    )


@pytest.fixture()
async def _test_invoice_creator_user_not_exist(
    active_session: ActiveSession,
    mub_client: TestClient,
) -> None:
    assert_nodata_response(
        mub_client.get(
            "/mub/invoice-service/users/999/invoices",
            params={"offset": 0, "limit": 50},
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
    )


@pytest.fixture()
async def _test_invoice_delete(
    active_session: ActiveSession, mub_client: TestClient, invoice: Invoice
) -> None:
    assert_nodata_response(
        mub_client.delete(f"/mub/invoice-service/invoices/{invoice.id}"),
    )
    async with active_session():
        assert (await invoice.find_first_by_id(invoice.id)) is None
