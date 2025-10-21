from typing import Any

import pytest
from pydantic_marshals.contains import assert_contains
from starlette import status
from starlette.testclient import TestClient

from app.invoices.models.recipient_invoices_db import (
    PaymentStatus,
    RecipientInvoice,
)
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.polyfactory_ext import BaseModelFactory
from tests.common.types import AnyJSON
from tests.invoices.factories import RecipientInvoicePaymentFactory

pytestmark = pytest.mark.anyio


async def test_student_recipient_invoice_retrieving(
    tutor_id: int,
    student_client: TestClient,
    recipient_invoice: RecipientInvoice,
    invoice_data_base_schema: AnyJSON,
    invoice_item_data_input_schema: AnyJSON,
    recipient_invoice_data: AnyJSON,
) -> None:
    assert_response(
        student_client.get(
            "/api/protected/invoice-service/roles/student"
            f"/recipient-invoices/{recipient_invoice.id}/"
        ),
        expected_json={
            "invoice": invoice_data_base_schema,
            "recipient_invoice": recipient_invoice_data,
            "invoice_items": [invoice_item_data_input_schema],
            "tutor_id": tutor_id,
        },
    )


async def test_student_recipient_invoice_payment_confirmation(
    active_session: ActiveSession,
    student_client: TestClient,
    recipient_invoice: RecipientInvoice,
) -> None:
    payment_data = RecipientInvoicePaymentFactory.build_json()

    assert_nodata_response(
        student_client.post(
            "/api/protected/invoice-service/roles/student"
            f"/recipient-invoices/{recipient_invoice.id}/payment-confirmations/sender/",
            json=payment_data,
        )
    )

    async with active_session() as session:
        session.add(recipient_invoice)
        await session.refresh(recipient_invoice)
        assert_contains(
            recipient_invoice,
            {**payment_data, "status": PaymentStatus.WF_RECEIVER_CONFIRMATION},
        )


@pytest.mark.parametrize(
    "payment_status",
    [
        pytest.param(payment_status, id=payment_status.value)
        for payment_status in PaymentStatus
        if payment_status is not PaymentStatus.WF_SENDER_CONFIRMATION
    ],
)
async def test_student_recipient_invoice_invalid_confirmation(
    active_session: ActiveSession,
    student_client: TestClient,
    recipient_invoice: RecipientInvoice,
    payment_status: PaymentStatus,
) -> None:
    payment_data = RecipientInvoicePaymentFactory.build_json()

    async with active_session() as session:
        session.add(recipient_invoice)
        recipient_invoice.status = payment_status

    assert_response(
        student_client.post(
            "/api/protected/invoice-service/roles/student"
            f"/recipient-invoices/{recipient_invoice.id}/payment-confirmations/sender/",
            json=payment_data,
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={
            "detail": "Invalid payment confirmation for the current payment status"
        },
    )


student_recipient_invoice_requests_parametrization = pytest.mark.parametrize(
    ("method", "body_factory", "path"),
    [
        pytest.param("GET", None, "", id="retrieve"),
        pytest.param(
            "POST",
            RecipientInvoicePaymentFactory,
            "payment-confirmations/sender/",
            id="confirm-sending",
        ),
    ],
)


@student_recipient_invoice_requests_parametrization
async def test_student_recipient_invoice_not_finding(
    student_client: TestClient,
    deleted_recipient_invoice_id: int,
    method: str,
    body_factory: type[BaseModelFactory[Any]] | None,
    path: str,
) -> None:
    assert_response(
        student_client.request(
            method=method,
            url=(
                "/api/protected/invoice-service/roles/student"
                f"/recipient-invoices/{deleted_recipient_invoice_id}/{path}"
            ),
            json=body_factory and body_factory.build_json(),
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Recipient invoice not found"},
    )


@student_recipient_invoice_requests_parametrization
async def test_student_recipient_invoice_requesting_access_denied(
    outsider_client: TestClient,
    recipient_invoice: RecipientInvoice,
    method: str,
    body_factory: type[BaseModelFactory[Any]] | None,
    path: str,
) -> None:
    assert_response(
        outsider_client.request(
            method=method,
            url=(
                f"/api/protected/invoice-service/roles/student"
                f"/recipient-invoices/{recipient_invoice.id}/{path}"
            ),
            json=body_factory and body_factory.build_json(),
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_json={"detail": "Recipient invoice student access denied"},
    )
