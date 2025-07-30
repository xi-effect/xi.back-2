from typing import Any

import pytest
from pydantic_marshals.contains import assert_contains
from starlette import status
from starlette.testclient import TestClient

from app.invoices.models.recipient_invoices_db import PaymentStatus, RecipientInvoice
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.polyfactory_ext import BaseModelFactory
from tests.common.types import AnyJSON
from tests.invoices.factories import RecipientInvoicePatchFactory

pytestmark = pytest.mark.anyio


async def test_recipient_invoice_updating(
    tutor_client: TestClient,
    recipient_invoice: RecipientInvoice,
    recipient_invoice_data: AnyJSON,
) -> None:
    recipient_invoice_patch_data = RecipientInvoicePatchFactory.build_json()

    assert_response(
        tutor_client.patch(
            f"/api/protected/invoice-service/roles/tutor/recipient-invoices/{recipient_invoice.id}/",
            json=recipient_invoice_patch_data,
        ),
        expected_json={**recipient_invoice_data, **recipient_invoice_patch_data},
    )


async def test_recipient_invoice_confirm_payment_status_by_tutor(
    active_session: ActiveSession,
    tutor_client: TestClient,
    recipient_invoice: RecipientInvoice,
) -> None:
    assert_nodata_response(
        tutor_client.post(
            f"/api/protected/invoice-service/roles/tutor/recipient-invoices/{recipient_invoice.id}/payment-confirmation/"
        )
    )

    async with active_session() as session:
        session.add(recipient_invoice)
        await session.refresh(recipient_invoice)
        assert_contains(recipient_invoice, {"status": PaymentStatus.COMPLETE})

        await recipient_invoice.delete()


async def test_recipient_invoice_invalid_confirm_payment_status_by_tutor(
    active_session: ActiveSession,
    tutor_client: TestClient,
    recipient_invoice: RecipientInvoice,
) -> None:
    async with active_session() as session:
        session.add(recipient_invoice)
        recipient_invoice.status = PaymentStatus.COMPLETE

    assert_response(
        tutor_client.post(
            f"/api/protected/invoice-service/roles/tutor/recipient-invoices/{recipient_invoice.id}/payment-confirmation/"
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={"detail": "Payment already confirmed"},
    )


async def test_recipient_invoice_deleting(
    active_session: ActiveSession,
    tutor_client: TestClient,
    recipient_invoice: RecipientInvoice,
) -> None:
    assert_nodata_response(
        tutor_client.delete(
            f"/api/protected/invoice-service/roles/tutor/recipient-invoices/{recipient_invoice.id}/"
        )
    )

    async with active_session():
        assert await RecipientInvoice.find_first_by_id(recipient_invoice.id) is None


recipient_invoice_requests_params = [
    pytest.param("PATCH", RecipientInvoicePatchFactory, id="update"),
    pytest.param("DELETE", None, id="delete"),
]


@pytest.mark.parametrize(("method", "body_factory"), recipient_invoice_requests_params)
async def test_recipient_invoice_not_founding(
    tutor_client: TestClient,
    deleted_recipient_invoice_id: int,
    method: str,
    body_factory: type[BaseModelFactory[Any]] | None,
) -> None:
    assert_response(
        tutor_client.request(
            method=method,
            url=f"/api/protected/invoice-service/roles/tutor/recipient-invoices/{deleted_recipient_invoice_id}/",
            json=body_factory and body_factory.build_json(),
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Recipient invoice not found"},
    )


@pytest.mark.parametrize(("method", "body_factory"), recipient_invoice_requests_params)
async def test_recipient_invoice_access_denied(
    outsider_client: TestClient,
    recipient_invoice: RecipientInvoice,
    method: str,
    body_factory: type[BaseModelFactory[Any]] | None,
) -> None:
    assert_response(
        outsider_client.request(
            method=method,
            url=f"/api/protected/invoice-service/roles/tutor/recipient-invoices/{recipient_invoice.id}/",
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_json={"detail": "Recipient invoice access denied"},
    )
