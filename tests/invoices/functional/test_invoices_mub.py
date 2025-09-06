from collections.abc import AsyncIterator
from typing import Any

import pytest
from starlette import status
from starlette.testclient import TestClient

from app.invoices.models.invoices_db import Invoice
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.polyfactory_ext import BaseModelFactory
from tests.common.types import AnyJSON
from tests.invoices.factories import InvoiceInputFactory, InvoicePatchFactory

pytestmark = pytest.mark.anyio

INVOICES_LIST_SIZE = 5


@pytest.fixture()
async def invoices(
    active_session: ActiveSession, tutor_id: int
) -> AsyncIterator[list[Invoice]]:
    async with active_session():
        invoices: list[Invoice] = [
            await Invoice.create(
                **InvoiceInputFactory.build_python(),
                tutor_id=tutor_id,
            )
            for _ in range(INVOICES_LIST_SIZE)
        ]

    yield invoices

    async with active_session():
        for invoice in invoices:
            await invoice.delete()


@pytest.mark.parametrize(
    ("offset", "limit"),
    [
        pytest.param(0, INVOICES_LIST_SIZE, id="start_to_end"),
        pytest.param(INVOICES_LIST_SIZE // 2, INVOICES_LIST_SIZE, id="middle_to_end"),
        pytest.param(0, INVOICES_LIST_SIZE // 2, id="start_to_middle"),
    ],
)
async def test_invoices_listing(
    mub_client: TestClient,
    tutor_id: int,
    invoices: list[Invoice],
    offset: int,
    limit: int,
) -> None:
    assert_response(
        mub_client.get(
            f"/mub/invoice-service/users/{tutor_id}/invoices/",
            params={"offset": offset, "limit": limit},
        ),
        expected_json=[
            Invoice.ResponseSchema.model_validate(invoice).model_dump(mode="json")
            for invoice in invoices[offset:limit]
        ],
    )


async def test_invoice_updating(
    mub_client: TestClient, invoice: Invoice, invoice_data: AnyJSON
) -> None:
    invoice_patch_data = InvoicePatchFactory.build_json()
    assert_response(
        mub_client.patch(
            f"/mub/invoice-service/invoices/{invoice.id}/", json=invoice_patch_data
        ),
        expected_json={**invoice_data, **invoice_patch_data},
    )


async def test_invoice_deleting(
    active_session: ActiveSession, mub_client: TestClient, invoice: Invoice
) -> None:
    assert_nodata_response(
        mub_client.delete(f"/mub/invoice-service/invoices/{invoice.id}/"),
    )
    async with active_session():
        assert await Invoice.find_first_by_id(invoice.id) is None


@pytest.mark.parametrize(
    ("method", "body_factory"),
    [
        pytest.param("PATCH", InvoicePatchFactory, id="patch"),
        pytest.param("DELETE", None, id="delete"),
    ],
)
async def test_invoice_not_finding(
    mub_client: TestClient,
    deleted_invoice_id: int,
    method: str,
    body_factory: type[BaseModelFactory[Any]] | None,
) -> None:
    assert_response(
        mub_client.request(
            method,
            f"/mub/invoice-service/invoices/{deleted_invoice_id}/",
            json=body_factory and body_factory.build_json(),
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Invoice not found"},
    )
