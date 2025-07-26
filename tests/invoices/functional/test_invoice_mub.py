from decimal import Decimal

import pytest
from starlette import status
from starlette.testclient import TestClient

from app.invoices.models.invoices_db import Invoice
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.types import AnyJSON
from tests.invoices.factories import InvoiceInputFactory, InvoicePatchFactory

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
    total: Decimal,
) -> None:
    invoices_data: list[AnyJSON] = [
        InvoiceInputFactory().build_json() for _ in range(INVOICES_LIST_SIZE)
    ]

    async with active_session():
        invoices: list[Invoice] = [
            await Invoice.create(
                **invoice_data,
                total=total,
                creator_user_id=creator_user_id,
            )
            for invoice_data in invoices_data
        ]

    assert_response(
        mub_client.get(
            f"/mub/invoice/users/{creator_user_id}/invoices",
            params={"offset": offset, "limit": limit},
        ),
        expected_code=status.HTTP_200_OK,
        expected_json=[
            Invoice.ResponseSchema.model_validate(invoices[i]).model_dump(mode="json")
            for i in range(offset, limit)
        ],
    )


async def test_invoice_update(
    mub_client: TestClient, invoice: Invoice, invoice_data: AnyJSON
) -> None:
    invoice_patch_data = InvoicePatchFactory.build_json()
    assert_response(
        mub_client.patch(
            f"/mub/invoice/invoices/{invoice.id}", json=invoice_patch_data
        ),
        expected_json={**invoice_data, **invoice_patch_data},
    )


async def test_invoice_delete(
    active_session: ActiveSession, mub_client: TestClient, invoice: Invoice
) -> None:
    assert_nodata_response(
        mub_client.delete(f"/mub/invoice/invoices/{invoice.id}/"),
        expected_code=status.HTTP_204_NO_CONTENT,
    )
    async with active_session():
        assert (await invoice.find_first_by_id(invoice.id)) is None
