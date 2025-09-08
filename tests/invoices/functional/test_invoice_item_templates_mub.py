import pytest
from freezegun import freeze_time
from starlette import status
from starlette.testclient import TestClient

from app.common.utils.datetime import datetime_utc_now
from app.invoices.models.invoice_item_templates_db import InvoiceItemTemplate
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_response
from tests.invoices.factories import InvoiceItemTemplateInputFactory

pytestmark = pytest.mark.anyio


INVOICES_SIZE = 5


async def test_invoice_item_templates_listing(
    active_session: ActiveSession,
    mub_client: TestClient,
    tutor_id: int,
) -> None:

    async with active_session():
        invoices_template: list[InvoiceItemTemplate] = [
            await InvoiceItemTemplate.create(
                **InvoiceItemTemplateInputFactory.build_python(), tutor_id=tutor_id
            )
            for _ in range(INVOICES_SIZE)
        ]

    invoices_template.reverse()
    assert_response(
        mub_client.get(
            f"/mub/invoice-service/users/{tutor_id}/invoice-item-templates/"
        ),
        expected_json=[
            InvoiceItemTemplate.ResponseSchema.model_validate(invoice).model_dump(
                mode="json"
            )
            for invoice in invoices_template
        ],
    )


@freeze_time()
async def test_invoice_item_template_creation(
    active_session: ActiveSession, mub_client: TestClient, tutor_id: int
) -> None:
    invoice_item_template_input_data = InvoiceItemTemplateInputFactory.build_json()
    invoice_item_template_id: int = assert_response(
        mub_client.post(
            url=f"/mub/invoice-service/users/{tutor_id}/invoice-item-templates/",
            json=invoice_item_template_input_data,
        ),
        expected_code=status.HTTP_201_CREATED,
        expected_json={
            **invoice_item_template_input_data,
            "id": int,
            "tutor_id": tutor_id,
            "created_at": datetime_utc_now(),
            "updated_at": datetime_utc_now(),
        },
    ).json()["id"]

    async with active_session():
        invoice_item_template = await InvoiceItemTemplate.find_first_by_id(
            invoice_item_template_id
        )
        assert invoice_item_template is not None
        assert invoice_item_template.tutor_id == tutor_id
        await invoice_item_template.delete()
