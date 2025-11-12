from random import randint
from unittest.mock import AsyncMock, call

import pytest
from freezegun import freeze_time
from pydantic_marshals.contains import assert_contains
from respx import MockRouter
from starlette import status
from starlette.testclient import TestClient

from app.common.config import settings
from app.common.schemas.notifications_sch import (
    NotificationInputSchema,
    NotificationKind,
    RecipientInvoiceNotificationPayloadSchema,
)
from app.common.utils.datetime import datetime_utc_now
from app.invoices.models.invoice_items_db import InvoiceItem
from app.invoices.models.invoices_db import Invoice
from app.invoices.models.recipient_invoices_db import PaymentStatus, RecipientInvoice
from app.invoices.routes.invoices_tutor_rst import InvoiceFormSchema
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_response
from tests.common.respx_ext import assert_last_httpx_request
from tests.invoices import factories

pytestmark = pytest.mark.anyio


@freeze_time()
@pytest.mark.parametrize(
    ("include_all_students", "expected_recipient_invoice_count"),
    [
        pytest.param(True, 2, id="all_classroom_students"),
        pytest.param(False, 1, id="specific_classroom_students"),
    ],
)
async def test_invoice_creation(
    active_session: ActiveSession,
    send_notification_mock: AsyncMock,
    classrooms_respx_mock: MockRouter,
    tutor_client: TestClient,
    tutor_id: int,
    student_id: int,
    classroom_id: int,
    include_all_students: bool,
    expected_recipient_invoice_count: int,
) -> None:
    other_student_id: int = (
        randint(student_id + 1, 1000)
        if student_id < 1000
        else randint(999, student_id - 1)
    )

    invoice_data: Invoice.InputSchema = factories.InvoiceInputFactory.build()
    invoice_item_data: InvoiceItem.InputSchema = (
        factories.InvoiceItemInputFactory.build()
    )
    invoice_form_data = InvoiceFormSchema(
        invoice=invoice_data,
        items=[invoice_item_data],
        student_ids=None if include_all_students else [student_id],
    )

    classroom_bridge_mock = classrooms_respx_mock.get(
        path=f"/classrooms/{classroom_id}/students/"
    ).respond(json=[student_id, other_student_id])

    invoice_id: int = assert_response(
        tutor_client.post(
            "/api/protected/invoice-service/roles/tutor"
            f"/classrooms/{classroom_id}/invoices/",
            json=invoice_form_data.model_dump(mode="json"),
        ),
        expected_code=status.HTTP_201_CREATED,
        expected_json={"id": int},
    ).json()["id"]

    async with active_session():
        invoice = await Invoice.find_first_by_id(invoice_id)
        assert invoice is not None
        assert_contains(
            invoice,
            {
                "tutor_id": tutor_id,
                "classroom_id": classroom_id,
                "created_at": datetime_utc_now(),
                **invoice_data.model_dump(),
            },
        )

        invoice_items = await InvoiceItem.find_all_by_kwargs(invoice_id=invoice_id)
        assert len(invoice_items) == 1
        assert_contains(
            invoice_items[0],
            {
                "position": 0,
                **invoice_item_data.model_dump(),
            },
        )

        student_id_to_recipient_invoice = {
            recipient_invoice.student_id: recipient_invoice
            for recipient_invoice in await RecipientInvoice.find_all_by_kwargs(
                invoice_id=invoice_id
            )
        }

        assert len(student_id_to_recipient_invoice) == expected_recipient_invoice_count

        assert_contains(
            student_id_to_recipient_invoice.get(student_id),
            {"status": PaymentStatus.WF_SENDER_CONFIRMATION},
        )
        if include_all_students:
            assert_contains(
                student_id_to_recipient_invoice.get(other_student_id),
                {"status": PaymentStatus.WF_SENDER_CONFIRMATION},
            )

        await invoice.delete()

    send_notification_mock.assert_has_awaits(
        [
            call(
                NotificationInputSchema(
                    payload=RecipientInvoiceNotificationPayloadSchema(
                        kind=NotificationKind.RECIPIENT_INVOICE_CREATED_V1,
                        recipient_invoice_id=recipient_invoice.id,
                    ),
                    recipient_user_ids=[recipient_invoice.student_id],
                )
            )
            for recipient_invoice in student_id_to_recipient_invoice.values()
        ]
    )

    assert_last_httpx_request(
        classroom_bridge_mock,
        expected_headers={"X-Api-Key": settings.api_key},
    )


async def test_invoice_creation_student_not_found(
    classrooms_respx_mock: MockRouter,
    tutor_client: TestClient,
    student_id: int,
    classroom_id: int,
) -> None:
    classroom_bridge_mock = classrooms_respx_mock.get(
        path=f"/classrooms/{classroom_id}/students/"
    ).respond(json=[])

    assert_response(
        tutor_client.post(
            "/api/protected/invoice-service/roles/tutor"
            f"/classrooms/{classroom_id}/invoices/",
            json=factories.InvoiceFormFactory.build_json(
                student_ids=[student_id],
            ),
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Student not found"},
    )

    assert_last_httpx_request(
        classroom_bridge_mock,
        expected_headers={"X-Api-Key": settings.api_key},
    )
