import pytest
from starlette.testclient import TestClient

from app.invoices.models.recipient_invoices_db import RecipientInvoice
from tests.common.assert_contains_ext import assert_response
from tests.common.utils import remove_none_values
from tests.invoices.conftest import TUTOR_INVOICE_LIST_SIZE

pytestmark = pytest.mark.anyio


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
