import pytest
from starlette import status
from starlette.testclient import TestClient

from app.invoices.models.recipient_invoices_db import RecipientInvoice
from tests.common.assert_contains_ext import assert_response
from tests.common.types import AnyJSON

pytestmark = pytest.mark.anyio


async def test_student_recipient_invoice_retrieving(
    tutor_id: int,
    student_client: TestClient,
    recipient_invoice: RecipientInvoice,
    invoice_comment_data: AnyJSON,
    invoice_item_data: AnyJSON,
) -> None:
    assert_response(
        student_client.get(
            f"/api/protected/invoice-service/roles/student/recipient-invoices/{recipient_invoice.id}/"
        ),
        expected_json={
            "invoice": invoice_comment_data,
            "items": [invoice_item_data],
            "tutor_id": tutor_id,
        },
    )


async def test_student_recipient_invoice_not_finding(
    student_client: TestClient,
    deleted_recipient_invoice_id: int,
) -> None:
    assert_response(
        student_client.get(
            url=f"/api/protected/invoice-service/roles/student/recipient-invoices/{deleted_recipient_invoice_id}/",
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Recipient invoice not found"},
    )


async def test_student_recipient_invoice_access_denied(
    outsider_client: TestClient,
    recipient_invoice: RecipientInvoice,
) -> None:
    assert_response(
        outsider_client.get(
            url=f"/api/protected/invoice-service/roles/student/recipient-invoices/{recipient_invoice.id}/",
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_json={"detail": "Recipient invoice student access denied"},
    )
