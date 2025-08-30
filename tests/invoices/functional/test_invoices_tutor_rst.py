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
from tests.invoices.factories import (
    RecipientInvoicePatchFactory,
    RecipientInvoicePaymentFactory,
)

pytestmark = pytest.mark.anyio


async def test_tutor_recipient_invoice_retrieving(
    tutor_client: TestClient,
    student_id: int,
    recipient_invoice: RecipientInvoice,
    invoice_data_base_schema: AnyJSON,
    invoice_item_data_input_schema: AnyJSON,
    recipient_invoice_data: AnyJSON,
) -> None:
    assert_response(
        tutor_client.get(
            f"/api/protected/invoice-service/roles/tutor/recipient-invoices/{recipient_invoice.id}/"
        ),
        expected_json={
            "invoice": invoice_data_base_schema,
            "recipient_invoice": recipient_invoice_data,
            "invoice_items": [invoice_item_data_input_schema],
            "student_id": student_id,
        },
    )


async def test_tutor_recipient_invoice_updating(
    tutor_client: TestClient,
    recipient_invoice: RecipientInvoice,
    recipient_invoice_tutor_data: AnyJSON,
) -> None:
    recipient_invoice_patch_data = RecipientInvoicePatchFactory.build_json()

    assert_response(
        tutor_client.patch(
            f"/api/protected/invoice-service/roles/tutor/recipient-invoices/{recipient_invoice.id}/",
            json=recipient_invoice_patch_data,
        ),
        expected_json={**recipient_invoice_tutor_data, **recipient_invoice_patch_data},
    )


async def test_tutor_recipient_invoice_unilateral_confirmation(
    active_session: ActiveSession,
    tutor_client: TestClient,
    recipient_invoice: RecipientInvoice,
) -> None:
    payment_data = RecipientInvoicePaymentFactory.build_json()

    assert_nodata_response(
        tutor_client.post(
            f"/api/protected/invoice-service/roles/tutor/recipient-invoices/{recipient_invoice.id}/payment-confirmations/unilateral/",
            json=payment_data,
        )
    )

    async with active_session() as session:
        session.add(recipient_invoice)
        await session.refresh(recipient_invoice)
        assert_contains(
            recipient_invoice,
            {**payment_data, "status": PaymentStatus.COMPLETE},
        )


@pytest.mark.parametrize(
    "payment_status",
    [
        pytest.param(PaymentStatus.COMPLETE),
        pytest.param(PaymentStatus.WF_RECEIVER_CONFIRMATION),
    ],
)
async def test_tutor_recipient_invoice_unilaterally_invalid_confirmation_unilaterally(
    active_session: ActiveSession,
    tutor_client: TestClient,
    recipient_invoice: RecipientInvoice,
    payment_status: PaymentStatus,
) -> None:
    async with active_session() as session:
        session.add(recipient_invoice)
        recipient_invoice.status = payment_status

    payment_data = RecipientInvoicePaymentFactory.build_json()

    assert_response(
        tutor_client.post(
            f"/api/protected/invoice-service/roles/tutor/recipient-invoices/{recipient_invoice.id}/payment-confirmations/unilateral/",
            json=payment_data,
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={
            "detail": "Invalid payment confirmation for the current payment status"
        },
    )


async def test_tutor_recipient_invoice_receiver_confirmation(
    active_session: ActiveSession,
    tutor_client: TestClient,
    recipient_invoice: RecipientInvoice,
) -> None:
    async with active_session() as session:
        session.add(recipient_invoice)
        recipient_invoice.status = PaymentStatus.WF_RECEIVER_CONFIRMATION

    assert_nodata_response(
        tutor_client.post(
            f"/api/protected/invoice-service/roles/tutor/recipient-invoices/{recipient_invoice.id}/payment-confirmations/receiver/"
        )
    )

    async with active_session() as session:
        session.add(recipient_invoice)
        await session.refresh(recipient_invoice)
        assert_contains(recipient_invoice, {"status": PaymentStatus.COMPLETE})


@pytest.mark.parametrize(
    "payment_status",
    [
        pytest.param(PaymentStatus.COMPLETE, id="complete"),
        pytest.param(PaymentStatus.WF_SENDER_CONFIRMATION, id="wf_sender_confirmation"),
    ],
)
async def test_tutor_recipient_invoice_invalid_confirmation_receiver(
    active_session: ActiveSession,
    tutor_client: TestClient,
    recipient_invoice: RecipientInvoice,
    payment_status: PaymentStatus,
) -> None:
    async with active_session() as session:
        session.add(recipient_invoice)
        recipient_invoice.status = payment_status

    assert_response(
        tutor_client.post(
            f"/api/protected/invoice-service/roles/tutor/recipient-invoices/{recipient_invoice.id}/payment-confirmations/receiver/",
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={
            "detail": "Invalid payment confirmation for the current payment status"
        },
    )


async def test_tutor_recipient_invoice_deleting(
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


tutor_recipient_invoice_requests_parametrization = pytest.mark.parametrize(
    ("method", "body_factory", "path"),
    [
        pytest.param("GET", None, "", id="retrieve"),
        pytest.param("PATCH", RecipientInvoicePatchFactory, "", id="update"),
        pytest.param("DELETE", None, "", id="delete"),
        pytest.param(
            "POST",
            RecipientInvoicePaymentFactory,
            "payment-confirmations/unilateral/",
            id="confirm-unilaterally",
        ),
        pytest.param(
            "POST", None, "payment-confirmations/receiver/", id="confirm-receiving"
        ),
    ],
)


@tutor_recipient_invoice_requests_parametrization
async def test_tutor_recipient_invoice_not_finding(
    tutor_client: TestClient,
    deleted_recipient_invoice_id: int,
    method: str,
    body_factory: type[BaseModelFactory[Any]] | None,
    path: str,
) -> None:
    assert_response(
        tutor_client.request(
            method=method,
            url=f"/api/protected/invoice-service/roles/tutor/recipient-invoices/{deleted_recipient_invoice_id}/{path}",
            json=body_factory and body_factory.build_json(),
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Recipient invoice not found"},
    )


@tutor_recipient_invoice_requests_parametrization
async def test_tutor_recipient_invoice_requesting_access_denied(
    outsider_client: TestClient,
    recipient_invoice: RecipientInvoice,
    method: str,
    body_factory: type[BaseModelFactory[Any]] | None,
    path: str,
) -> None:
    assert_response(
        outsider_client.request(
            method=method,
            url=f"/api/protected/invoice-service/roles/tutor/recipient-invoices/{recipient_invoice.id}/{path}",
            json=body_factory and body_factory.build_json(),
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_json={"detail": "Recipient invoice tutor access denied"},
    )
