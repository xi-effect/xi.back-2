from unittest.mock import Mock

import pytest
from pydantic_marshals.contains import assert_contains

from app.common.schemas import notifications_sch, pochta_sch
from app.notifications.services.adapters.email_message_adapter import (
    NotificationToEmailMessageAdapter,
)
from tests.notifications import factories

pytestmark = pytest.mark.anyio


async def test_individual_invitation_accepted_v1_notification_adapting(
    notification_mock: Mock,
) -> None:
    notification_payload: (
        notifications_sch.InvitationAcceptanceNotificationPayloadSchema
    ) = factories.InvitationAcceptanceNotificationPayloadFactory.build(
        kind=notifications_sch.NotificationKind.INDIVIDUAL_INVITATION_ACCEPTED_V1
    )
    notification_mock.payload = notification_payload

    email_notification_adapter = NotificationToEmailMessageAdapter(
        notification=notification_mock
    )

    assert_contains(
        email_notification_adapter.adapt(),
        pochta_sch.ClassroomNotificationEmailMessagePayloadSchema(
            kind=pochta_sch.EmailMessageKind.INDIVIDUAL_INVITATION_ACCEPTED_V1,
            classroom_id=notification_payload.classroom_id,
            notification_id=notification_mock.id,
        ).model_dump(),
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

    email_notification_adapter = NotificationToEmailMessageAdapter(
        notification=notification_mock
    )

    assert_contains(
        email_notification_adapter.adapt(),
        pochta_sch.ClassroomNotificationEmailMessagePayloadSchema(
            kind=pochta_sch.EmailMessageKind.GROUP_INVITATION_ACCEPTED_V1,
            classroom_id=notification_payload.classroom_id,
            notification_id=notification_mock.id,
        ).model_dump(),
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

    email_notification_adapter = NotificationToEmailMessageAdapter(
        notification=notification_mock
    )

    assert_contains(
        email_notification_adapter.adapt(),
        pochta_sch.ClassroomNotificationEmailMessagePayloadSchema(
            kind=pochta_sch.EmailMessageKind.ENROLLMENT_CREATED_V1,
            classroom_id=notification_payload.classroom_id,
            notification_id=notification_mock.id,
        ).model_dump(),
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

    email_notification_adapter = NotificationToEmailMessageAdapter(
        notification=notification_mock
    )

    assert_contains(
        email_notification_adapter.adapt(),
        pochta_sch.ClassroomNotificationEmailMessagePayloadSchema(
            kind=pochta_sch.EmailMessageKind.CLASSROOM_CONFERENCE_STARTED_V1,
            classroom_id=notification_payload.classroom_id,
            notification_id=notification_mock.id,
        ).model_dump(),
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

    email_notification_adapter = NotificationToEmailMessageAdapter(
        notification=notification_mock
    )

    assert_contains(
        email_notification_adapter.adapt(),
        pochta_sch.RecipientInvoiceNotificationEmailMessagePayloadSchema(
            kind=pochta_sch.EmailMessageKind.RECIPIENT_INVOICE_CREATED_V1,
            recipient_invoice_id=notification_payload.recipient_invoice_id,
            notification_id=notification_mock.id,
        ).model_dump(),
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

    email_notification_adapter = NotificationToEmailMessageAdapter(
        notification=notification_mock
    )

    assert_contains(
        email_notification_adapter.adapt(),
        pochta_sch.RecipientInvoiceNotificationEmailMessagePayloadSchema(
            kind=pochta_sch.EmailMessageKind.STUDENT_RECIPIENT_INVOICE_PAYMENT_CONFIRMED_V1,
            recipient_invoice_id=notification_payload.recipient_invoice_id,
            notification_id=notification_mock.id,
        ).model_dump(),
    )
