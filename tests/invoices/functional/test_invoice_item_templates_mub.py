from typing import Any

import pytest
from freezegun import freeze_time
from starlette import status
from starlette.testclient import TestClient

from app.common.utils.datetime import datetime_utc_now
from app.invoices.models.invoice_item_templates_db import InvoiceItemTemplate
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import (
    assert_nodata_response,
    assert_response,
)
from tests.common.mock_stack import MockStack
from tests.common.polyfactory_ext import BaseModelFactory
from tests.common.types import AnyJSON
from tests.invoices.factories import (
    InvoiceItemTemplateInputFactory,
    InvoiceItemTemplatePatchFactory,
)

pytestmark = pytest.mark.anyio


async def test_invoice_item_templates_listing(
    mub_client: TestClient,
    tutor_id: int,
    invoice_item_template_data: AnyJSON,
) -> None:
    assert_response(
        mub_client.get(
            f"/mub/invoice-service/users/{tutor_id}/invoice-item-templates/"
        ),
        expected_json=[invoice_item_template_data],
    )


@freeze_time()
async def test_invoice_item_template_creation(
    active_session: ActiveSession,
    mub_client: TestClient,
    tutor_id: int,
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


async def test_invoice_item_template_creation_quantity_exceeded(
    mock_stack: MockStack, mub_client: TestClient, tutor_id: int
) -> None:
    mock_stack.enter_mock(InvoiceItemTemplate, "max_count_per_user", property_value=0)

    assert_response(
        mub_client.post(
            f"/mub/invoice-service/users/{tutor_id}/invoice-item-templates/",
            json=InvoiceItemTemplateInputFactory.build_json(),
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={"detail": "Quantity exceeded"},
    )


async def test_invoice_item_template_retrieving(
    mub_client: TestClient, invoice_item_template_data: AnyJSON
) -> None:
    assert_response(
        mub_client.get(
            f"/mub/invoice-service/invoice-item-templates/{invoice_item_template_data["id"]}/"
        ),
        expected_json=invoice_item_template_data,
    )


@freeze_time()
async def test_invoice_item_template_updating(
    mub_client: TestClient,
    invoice_item_template_data: AnyJSON,
) -> None:
    invoice_item_template_patch_data = InvoiceItemTemplatePatchFactory.build_json()

    assert_response(
        mub_client.patch(
            f"/mub/invoice-service/invoice-item-templates/{invoice_item_template_data["id"]}/",
            json=invoice_item_template_patch_data,
        ),
        expected_json={
            **invoice_item_template_data,
            **invoice_item_template_patch_data,
            "updated_at": datetime_utc_now(),
        },
    )


async def test_invoice_item_template_deleting(
    active_session: ActiveSession,
    mub_client: TestClient,
    invoice_item_template: InvoiceItemTemplate,
) -> None:
    assert_nodata_response(
        mub_client.delete(
            f"/mub/invoice-service/invoice-item-templates/{invoice_item_template.id}/"
        )
    )

    async with active_session():
        assert (
            await InvoiceItemTemplate.find_first_by_id(invoice_item_template.id) is None
        )


@pytest.mark.parametrize(
    ("method", "body_factory"),
    [
        pytest.param("GET", None, id="retrieve"),
        pytest.param("PATCH", InvoiceItemTemplatePatchFactory, id="update"),
        pytest.param("DELETE", None, id="delete"),
    ],
)
async def test_invoice_item_template_not_finding(
    mub_client: TestClient,
    deleted_invoice_item_template_id: int,
    method: str,
    body_factory: type[BaseModelFactory[Any]] | None,
) -> None:
    assert_response(
        mub_client.request(
            method=method,
            url=f"/mub/invoice-service/invoice-item-templates/{deleted_invoice_item_template_id}/",
            json=body_factory and body_factory.build_json(),
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Invoice item template not found"},
    )
