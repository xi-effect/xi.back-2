from unittest.mock import Mock

import pytest

from app.common.schemas import notifications_sch
from app.notifications import texts
from app.notifications.services.notification_adapters.recipient_invoice_notification_adapters import (
    RecipientInvoiceCreatedV1NotificationAdapter,
    StudentRecipientInvoicePaymentConfirmedV1NotificationAdapter,
)
from tests.notifications import factories
from tests.notifications.utils import (
    assert_messenger_message_payload,
    assert_universal_email_message_payload,
)

pytestmark = pytest.mark.anyio


async def test_recipient_invoice_created_v1_messenger_adapting(
    notification_mock: Mock,
) -> None:
    notification_payload: (
        notifications_sch.RecipientInvoiceNotificationPayloadSchema
    ) = factories.RecipientInvoiceNotificationPayloadFactory.build(
        kind=notifications_sch.NotificationKind.RECIPIENT_INVOICE_CREATED_V1,
    )

    notification_adapter = RecipientInvoiceCreatedV1NotificationAdapter(
        notification=notification_mock,
        payload=notification_payload,
    )

    assert_messenger_message_payload(
        notification_adapter.to_messenger_message_payload(),
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


async def test_recipient_invoice_created_v1_email_adapting(
    notification_mock: Mock,
) -> None:
    notification_payload: (
        notifications_sch.RecipientInvoiceNotificationPayloadSchema
    ) = factories.RecipientInvoiceNotificationPayloadFactory.build(
        kind=notifications_sch.NotificationKind.RECIPIENT_INVOICE_CREATED_V1,
    )

    notification_adapter = RecipientInvoiceCreatedV1NotificationAdapter(
        notification=notification_mock,
        payload=notification_payload,
    )

    assert_universal_email_message_payload(
        notification_adapter.to_universal_email_message_payload(),
        expected_notification_id=notification_mock.id,
        expected_theme=texts.RECIPIENT_INVOICE_CREATED_V1_EMAIL_THEME,
        expected_pre_header=texts.RECIPIENT_INVOICE_CREATED_V1_EMAIL_PRE_HEADER,
        expected_header=texts.RECIPIENT_INVOICE_CREATED_V1_EMAIL_HEADER,
        expected_content=texts.RECIPIENT_INVOICE_CREATED_V1_EMAIL_CONTENT,
        expected_button_text=texts.RECIPIENT_INVOICE_CREATED_V1_BUTTON_TEXT,
        expected_button_link_path="/payments",
        expected_button_link_query={
            "tab": ["invoices"],
            "role": ["student"],
            "recipient_invoice_id": [str(notification_payload.recipient_invoice_id)],
        },
    )


async def test_student_recipient_invoice_payment_confirmed_v1_messenger_adapting(
    notification_mock: Mock,
) -> None:
    notification_payload: (
        notifications_sch.RecipientInvoiceNotificationPayloadSchema
    ) = factories.RecipientInvoiceNotificationPayloadFactory.build(
        kind=notifications_sch.NotificationKind.STUDENT_RECIPIENT_INVOICE_PAYMENT_CONFIRMED_V1,
    )

    notification_adapter = StudentRecipientInvoicePaymentConfirmedV1NotificationAdapter(
        notification=notification_mock,
        payload=notification_payload,
    )

    assert_messenger_message_payload(
        notification_adapter.to_messenger_message_payload(),
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


async def test_student_recipient_invoice_payment_confirmed_v1_email_adapting(
    notification_mock: Mock,
) -> None:
    notification_payload: (
        notifications_sch.RecipientInvoiceNotificationPayloadSchema
    ) = factories.RecipientInvoiceNotificationPayloadFactory.build(
        kind=notifications_sch.NotificationKind.STUDENT_RECIPIENT_INVOICE_PAYMENT_CONFIRMED_V1,
    )

    notification_adapter = StudentRecipientInvoicePaymentConfirmedV1NotificationAdapter(
        notification=notification_mock,
        payload=notification_payload,
    )

    assert_universal_email_message_payload(
        notification_adapter.to_universal_email_message_payload(),
        expected_notification_id=notification_mock.id,
        expected_theme=texts.STUDENT_RECIPIENT_INVOICE_PAYMENT_CONFIRMED_V1_EMAIL_THEME,
        expected_pre_header=texts.STUDENT_RECIPIENT_INVOICE_PAYMENT_CONFIRMED_V1_EMAIL_PRE_HEADER,
        expected_header=texts.STUDENT_RECIPIENT_INVOICE_PAYMENT_CONFIRMED_V1_EMAIL_HEADER,
        expected_content=texts.STUDENT_RECIPIENT_INVOICE_PAYMENT_CONFIRMED_V1_EMAIL_CONTENT,
        expected_button_text=texts.STUDENT_RECIPIENT_INVOICE_PAYMENT_CONFIRMED_V1_BUTTON_TEXT,
        expected_button_link_path="/payments",
        expected_button_link_query={
            "tab": ["invoices"],
            "role": ["tutor"],
            "recipient_invoice_id": [str(notification_payload.recipient_invoice_id)],
        },
    )
