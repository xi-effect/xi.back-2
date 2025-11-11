from typing import Any
from unittest.mock import Mock
from urllib.parse import parse_qs, urlparse
from uuid import UUID, uuid4

import pytest
from pydantic import HttpUrl
from pydantic_marshals.contains import assert_contains

from app.common.config import settings
from app.common.schemas import notifications_sch
from app.notifications import texts
from app.notifications.services.adapters.telegram_message_adapter import (
    NotificationToTelegramMessageAdapter,
    TelegramMessagePayloadSchema,
)
from tests.notifications import factories

pytestmark = pytest.mark.anyio


@pytest.fixture()
def notification_mock() -> Mock:
    notification_mock = Mock()
    notification_mock.id = uuid4()
    return notification_mock


def assert_telegram_message_payload(
    telegram_message_payload: TelegramMessagePayloadSchema,
    expected_notification_id: UUID,
    expected_message_text: str,
    expected_button_text: str,
    expected_button_link_path: str,
    expected_button_link_query: dict[str, list[Any]],
) -> None:
    assert_contains(
        telegram_message_payload,
        {
            "message_text": expected_message_text,
            "button_text": expected_button_text,
            "button_link": HttpUrl,
        },
    )

    assert telegram_message_payload.button_link.startswith(
        settings.frontend_app_base_url
    )
    parsed_button_link = urlparse(telegram_message_payload.button_link)
    assert_contains(
        {
            "path": parsed_button_link.path,
            "query": parse_qs(parsed_button_link.query),
        },
        {
            "path": expected_button_link_path,
            "query": {
                **expected_button_link_query,
                "read_notification_id": [expected_notification_id],
            },
        },
    )


async def test_individual_invitation_accepted_v1_notification_adapting(
    notification_mock: Mock,
) -> None:
    notification_payload: (
        notifications_sch.InvitationAcceptanceNotificationPayloadSchema
    ) = factories.InvitationAcceptanceNotificationPayloadFactory.build(
        kind=notifications_sch.NotificationKind.INDIVIDUAL_INVITATION_ACCEPTED_V1
    )
    notification_mock.payload = notification_payload

    telegram_notification_adapter = NotificationToTelegramMessageAdapter(
        notification=notification_mock
    )

    assert_telegram_message_payload(
        telegram_notification_adapter.adapt(),
        expected_notification_id=notification_mock.id,
        expected_message_text=texts.INDIVIDUAL_INVITATION_ACCEPTED_V1_MESSAGE,
        expected_button_text=texts.INDIVIDUAL_INVITATION_ACCEPTED_V1_BUTTON_TEXT,
        expected_button_link_path=f"/classrooms/{notification_payload.classroom_id}",
        expected_button_link_query={
            "tab": ["overview"],
            "role": ["tutor"],
        },
    )


async def test_group_invitation_accepted_v1_notification_adapting(
    notification_mock: Mock,
) -> None:
    notification_payload: (
        notifications_sch.InvitationAcceptanceNotificationPayloadSchema
    ) = factories.InvitationAcceptanceNotificationPayloadFactory.build(
        kind=notifications_sch.NotificationKind.GROUP_INVITATION_ACCEPTED_V1
    )
    notification_mock.payload = notification_payload

    telegram_notification_adapter = NotificationToTelegramMessageAdapter(
        notification=notification_mock
    )

    assert_telegram_message_payload(
        telegram_notification_adapter.adapt(),
        expected_notification_id=notification_mock.id,
        expected_message_text=texts.GROUP_INVITATION_ACCEPTED_V1_MESSAGE,
        expected_button_text=texts.GROUP_INVITATION_ACCEPTED_V1_BUTTON_TEXT,
        expected_button_link_path=f"/classrooms/{notification_payload.classroom_id}",
        expected_button_link_query={
            "tab": ["overview"],
            "role": ["tutor"],
        },
    )


async def test_group_enrollment_created_v1_notification_adapting(
    notification_mock: Mock,
) -> None:
    notification_payload: notifications_sch.EnrollmentNotificationPayloadSchema = (
        factories.EnrollmentNotificationPayloadFactory.build(
            kind=notifications_sch.NotificationKind.ENROLLMENT_CREATED_V1
        )
    )
    notification_mock.payload = notification_payload

    telegram_notification_adapter = NotificationToTelegramMessageAdapter(
        notification=notification_mock
    )

    assert_telegram_message_payload(
        telegram_notification_adapter.adapt(),
        expected_notification_id=notification_mock.id,
        expected_message_text=texts.ENROLLMENT_CREATED_V1_MESSAGE,
        expected_button_text=texts.ENROLLMENT_CREATED_V1_BUTTON_TEXT,
        expected_button_link_path=f"/classrooms/{notification_payload.classroom_id}",
        expected_button_link_query={
            "tab": ["overview"],
            "role": ["student"],
        },
    )


async def test_classroom_conference_started_v1_notification_adapting(
    notification_mock: Mock,
) -> None:
    notification_payload: notifications_sch.ClassroomNotificationPayloadSchema = (
        factories.ClassroomNotificationPayloadFactory.build(
            kind=notifications_sch.NotificationKind.CLASSROOM_CONFERENCE_STARTED_V1
        )
    )
    notification_mock.payload = notification_payload

    telegram_notification_adapter = NotificationToTelegramMessageAdapter(
        notification=notification_mock
    )

    assert_telegram_message_payload(
        telegram_notification_adapter.adapt(),
        expected_notification_id=notification_mock.id,
        expected_message_text=texts.CLASSROOM_CONFERENCE_STARTED_V1_MESSAGE,
        expected_button_text=texts.CLASSROOM_CONFERENCE_STARTED_V1_BUTTON_TEXT,
        expected_button_link_path=f"/classrooms/{notification_payload.classroom_id}",
        expected_button_link_query={
            "tab": ["overview"],
            "role": ["student"],
            "goto": ["call"],
        },
    )


async def test_recipient_invoice_created_v1_notification_adapting(
    notification_mock: Mock,
) -> None:
    notification_payload: (
        notifications_sch.RecipientInvoiceNotificationPayloadSchema
    ) = factories.RecipientInvoiceNotificationPayloadFactory.build(
        kind=notifications_sch.NotificationKind.RECIPIENT_INVOICE_CREATED_V1
    )
    notification_mock.payload = notification_payload

    telegram_notification_adapter = NotificationToTelegramMessageAdapter(
        notification=notification_mock
    )

    assert_telegram_message_payload(
        telegram_notification_adapter.adapt(),
        expected_notification_id=notification_mock.id,
        expected_message_text=texts.RECIPIENT_INVOICE_CREATED_V1_MESSAGE,
        expected_button_text=texts.RECIPIENT_INVOICE_CREATED_V1_BUTTON_TEXT,
        expected_button_link_path="/payments",
        expected_button_link_query={
            "tab": ["invoices"],
            "role": ["student"],
            "recipient_invoice_id": [str(notification_payload.recipient_invoice_id)],
        },
    )


async def test_student_recipient_invoice_payment_confirmed_v1_notification_adapting(
    notification_mock: Mock,
) -> None:
    notification_payload: (
        notifications_sch.RecipientInvoiceNotificationPayloadSchema
    ) = factories.RecipientInvoiceNotificationPayloadFactory.build(
        kind=notifications_sch.NotificationKind.STUDENT_RECIPIENT_INVOICE_PAYMENT_CONFIRMED_V1
    )
    notification_mock.payload = notification_payload

    telegram_notification_adapter = NotificationToTelegramMessageAdapter(
        notification=notification_mock
    )

    assert_telegram_message_payload(
        telegram_notification_adapter.adapt(),
        expected_notification_id=notification_mock.id,
        expected_message_text=texts.STUDENT_RECIPIENT_INVOICE_PAYMENT_CONFIRMED_V1_MESSAGE,
        expected_button_text=texts.STUDENT_RECIPIENT_INVOICE_PAYMENT_CONFIRMED_V1_BUTTON_TEXT,
        expected_button_link_path="/payments",
        expected_button_link_query={
            "tab": ["invoices"],
            "role": ["tutor"],
            "recipient_invoice_id": [str(notification_payload.recipient_invoice_id)],
        },
    )
