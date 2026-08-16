from typing import Any
from unittest.mock import Mock
from urllib.parse import parse_qs, urlparse
from uuid import UUID

import pytest
from pydantic import HttpUrl
from pydantic_marshals.contains import assert_contains

from app.common.config import settings
from app.common.schemas import notifications_sch, pochta_sch
from app.notifications import texts
from app.notifications.services.notification_adapters.email_notification_adapter import (
    EmailNotificationAdapter,
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

    email_notification_adapter = EmailNotificationAdapter(
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

    email_notification_adapter = EmailNotificationAdapter(
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

    email_notification_adapter = EmailNotificationAdapter(
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

    email_notification_adapter = EmailNotificationAdapter(
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

    email_notification_adapter = EmailNotificationAdapter(
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

    email_notification_adapter = EmailNotificationAdapter(
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


def assert_universal_email_message_payload(
    universal_email_message_payload: pochta_sch.UniversalEmailMessagePayloadSchema,
    expected_notification_id: UUID,
    expected_theme: str,
    expected_pre_header: str,
    expected_header: str,
    expected_content: str,
    expected_button_text: str,
    expected_button_link_path: str,
    expected_button_link_query: dict[str, list[Any]],
) -> None:
    assert_contains(
        universal_email_message_payload,
        {
            "theme": expected_theme,
            "pre_header": expected_pre_header,
            "header": expected_header,
            "content": expected_content,
            "button_text": expected_button_text,
            "button_link": HttpUrl,
        },
    )

    assert universal_email_message_payload.button_link.startswith(
        settings.frontend_app_base_url
    )
    parsed_button_link = urlparse(universal_email_message_payload.button_link)
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


async def test_single_classroom_event_created_v1_adapting(
    notification_mock: Mock,
) -> None:
    notification_payload: (
        notifications_sch.PersistedClassroomEventInstanceNotificationPayloadSchema
    ) = factories.PersistedClassroomEventInstanceNotificationPayloadFactory.build(
        kind=notifications_sch.NotificationKind.SINGLE_CLASSROOM_EVENT_CREATED_V1
    )
    notification_mock.payload = notification_payload

    email_notification_adapter = EmailNotificationAdapter(
        notification=notification_mock
    )

    result = email_notification_adapter.adapt()
    assert isinstance(result, pochta_sch.UniversalEmailMessagePayloadSchema)

    assert_universal_email_message_payload(
        result,
        expected_notification_id=notification_mock.id,
        expected_theme=texts.SINGLE_CLASSROOM_EVENT_CREATED_V1_EMAIL_THEME,
        expected_pre_header=texts.SINGLE_CLASSROOM_EVENT_CREATED_V1_EMAIL_PRE_HEADER,
        expected_header=texts.SINGLE_CLASSROOM_EVENT_CREATED_V1_EMAIL_HEADER,
        expected_content=texts.SINGLE_CLASSROOM_EVENT_CREATED_V1_EMAIL_CONTENT,
        expected_button_text=texts.CLASSROOM_EVENT_INSTANCE_BUTTON_TEXT,
        expected_button_link_path=f"/classrooms/{notification_payload.classroom_id}",
        expected_button_link_query={
            "tab": ["schedule"],
            "event_instance_id": [str(notification_payload.event_instance_id)],
        },
    )


async def test_classroom_event_instance_rescheduled_v1_adapting(
    notification_mock: Mock,
) -> None:
    notification_payload: (
        notifications_sch.PersistedClassroomEventInstanceNotificationPayloadSchema
    ) = factories.PersistedClassroomEventInstanceNotificationPayloadFactory.build(
        kind=notifications_sch.NotificationKind.CLASSROOM_EVENT_INSTANCE_RESCHEDULED_V1
    )
    notification_mock.payload = notification_payload

    email_notification_adapter = EmailNotificationAdapter(
        notification=notification_mock
    )

    result = email_notification_adapter.adapt()
    assert isinstance(result, pochta_sch.UniversalEmailMessagePayloadSchema)

    assert_universal_email_message_payload(
        result,
        expected_notification_id=notification_mock.id,
        expected_theme=texts.CLASSROOM_EVENT_INSTANCE_RESCHEDULED_V1_EMAIL_THEME,
        expected_pre_header=texts.CLASSROOM_EVENT_INSTANCE_RESCHEDULED_V1_EMAIL_PRE_HEADER,
        expected_header=texts.CLASSROOM_EVENT_INSTANCE_RESCHEDULED_V1_EMAIL_HEADER,
        expected_content=texts.CLASSROOM_EVENT_INSTANCE_RESCHEDULED_V1_EMAIL_CONTENT,
        expected_button_text=texts.CLASSROOM_EVENT_INSTANCE_BUTTON_TEXT,
        expected_button_link_path=f"/classrooms/{notification_payload.classroom_id}",
        expected_button_link_query={
            "tab": ["schedule"],
            "event_instance_id": [str(notification_payload.event_instance_id)],
        },
    )


async def test_classroom_event_instance_cancelled_v1_adapting(
    notification_mock: Mock,
) -> None:
    notification_payload: (
        notifications_sch.PersistedClassroomEventInstanceNotificationPayloadSchema
    ) = factories.PersistedClassroomEventInstanceNotificationPayloadFactory.build(
        kind=notifications_sch.NotificationKind.CLASSROOM_EVENT_INSTANCE_CANCELLED_V1
    )
    notification_mock.payload = notification_payload

    email_notification_adapter = EmailNotificationAdapter(
        notification=notification_mock
    )

    result = email_notification_adapter.adapt()
    assert isinstance(result, pochta_sch.UniversalEmailMessagePayloadSchema)

    assert_universal_email_message_payload(
        result,
        expected_notification_id=notification_mock.id,
        expected_theme=texts.CLASSROOM_EVENT_INSTANCE_CANCELLED_V1_EMAIL_THEME,
        expected_pre_header=texts.CLASSROOM_EVENT_INSTANCE_CANCELLED_V1_EMAIL_PRE_HEADER,
        expected_header=texts.CLASSROOM_EVENT_INSTANCE_CANCELLED_V1_EMAIL_HEADER,
        expected_content=texts.CLASSROOM_EVENT_INSTANCE_CANCELLED_V1_EMAIL_CONTENT,
        expected_button_text=texts.CLASSROOM_EVENT_INSTANCE_BUTTON_TEXT,
        expected_button_link_path=f"/classrooms/{notification_payload.classroom_id}",
        expected_button_link_query={
            "tab": ["schedule"],
            "event_instance_id": [str(notification_payload.event_instance_id)],
        },
    )


async def test_persisted_classroom_event_instance_reminder_v1_adapting(
    notification_mock: Mock,
) -> None:
    notification_payload: (
        notifications_sch.PersistedClassroomEventInstanceNotificationPayloadSchema
    ) = factories.PersistedClassroomEventInstanceNotificationPayloadFactory.build(
        kind=notifications_sch.NotificationKind.PERSISTED_CLASSROOM_EVENT_INSTANCE_REMINDER_V1
    )
    notification_mock.payload = notification_payload

    email_notification_adapter = EmailNotificationAdapter(
        notification=notification_mock
    )

    result = email_notification_adapter.adapt()
    assert isinstance(result, pochta_sch.UniversalEmailMessagePayloadSchema)

    assert_universal_email_message_payload(
        result,
        expected_notification_id=notification_mock.id,
        expected_theme=texts.CLASSROOM_EVENT_INSTANCE_REMINDER_V1_EMAIL_THEME,
        expected_pre_header=texts.CLASSROOM_EVENT_INSTANCE_REMINDER_V1_EMAIL_PRE_HEADER,
        expected_header=texts.CLASSROOM_EVENT_INSTANCE_REMINDER_V1_EMAIL_HEADER,
        expected_content=texts.CLASSROOM_EVENT_INSTANCE_REMINDER_V1_EMAIL_CONTENT,
        expected_button_text=texts.CLASSROOM_EVENT_INSTANCE_BUTTON_TEXT,
        expected_button_link_path=f"/classrooms/{notification_payload.classroom_id}",
        expected_button_link_query={
            "tab": ["schedule"],
            "event_instance_id": [str(notification_payload.event_instance_id)],
        },
    )


async def test_repeated_classroom_event_instance_reminder_v1_adapting(
    notification_mock: Mock,
) -> None:
    notification_payload: (
        notifications_sch.RepeatedClassroomEventInstanceNotificationPayloadSchema
    ) = factories.RepeatedClassroomEventInstanceNotificationPayloadFactory.build(
        kind=notifications_sch.NotificationKind.REPEATED_CLASSROOM_EVENT_INSTANCE_REMINDER_V1
    )
    notification_mock.payload = notification_payload

    email_notification_adapter = EmailNotificationAdapter(
        notification=notification_mock
    )

    result = email_notification_adapter.adapt()
    assert isinstance(result, pochta_sch.UniversalEmailMessagePayloadSchema)

    assert_universal_email_message_payload(
        result,
        expected_notification_id=notification_mock.id,
        expected_theme=texts.CLASSROOM_EVENT_INSTANCE_REMINDER_V1_EMAIL_THEME,
        expected_pre_header=texts.CLASSROOM_EVENT_INSTANCE_REMINDER_V1_EMAIL_PRE_HEADER,
        expected_header=texts.CLASSROOM_EVENT_INSTANCE_REMINDER_V1_EMAIL_HEADER,
        expected_content=texts.CLASSROOM_EVENT_INSTANCE_REMINDER_V1_EMAIL_CONTENT,
        expected_button_text=texts.CLASSROOM_EVENT_INSTANCE_BUTTON_TEXT,
        expected_button_link_path=f"/classrooms/{notification_payload.classroom_id}",
        expected_button_link_query={
            "tab": ["schedule"],
            "repetition_mode_id": [str(notification_payload.repetition_mode_id)],
            "instance_index": [str(notification_payload.instance_index)],
        },
    )


async def test_repeating_classroom_event_created_v1_adapting(
    notification_mock: Mock,
) -> None:
    notification_payload: (
        notifications_sch.ClassroomScheduleFocusNotificationPayloadSchema
    ) = factories.ClassroomScheduleFocusNotificationPayloadFactory.build(
        kind=notifications_sch.NotificationKind.REPEATING_CLASSROOM_EVENT_CREATED_V1
    )
    notification_mock.payload = notification_payload

    email_notification_adapter = EmailNotificationAdapter(
        notification=notification_mock
    )

    result = email_notification_adapter.adapt()
    assert isinstance(result, pochta_sch.UniversalEmailMessagePayloadSchema)

    assert_universal_email_message_payload(
        result,
        expected_notification_id=notification_mock.id,
        expected_theme=texts.REPEATING_CLASSROOM_EVENT_CREATED_V1_EMAIL_THEME,
        expected_pre_header=texts.REPEATING_CLASSROOM_EVENT_CREATED_V1_EMAIL_PRE_HEADER,
        expected_header=texts.REPEATING_CLASSROOM_EVENT_CREATED_V1_EMAIL_HEADER,
        expected_content=texts.REPEATING_CLASSROOM_EVENT_CREATED_V1_EMAIL_CONTENT,
        expected_button_text=texts.CLASSROOM_SCHEDULE_FOCUS_BUTTON_TEXT,
        expected_button_link_path=f"/classrooms/{notification_payload.classroom_id}",
        expected_button_link_query={
            "tab": ["schedule"],
            "focused_at": [notification_payload.focused_at.isoformat()],
        },
    )


async def test_classroom_event_repetition_updated_v1_adapting(
    notification_mock: Mock,
) -> None:
    notification_payload: (
        notifications_sch.ClassroomScheduleFocusNotificationPayloadSchema
    ) = factories.ClassroomScheduleFocusNotificationPayloadFactory.build(
        kind=notifications_sch.NotificationKind.CLASSROOM_EVENT_REPETITION_UPDATED_V1
    )
    notification_mock.payload = notification_payload

    email_notification_adapter = EmailNotificationAdapter(
        notification=notification_mock
    )

    result = email_notification_adapter.adapt()
    assert isinstance(result, pochta_sch.UniversalEmailMessagePayloadSchema)

    assert_universal_email_message_payload(
        result,
        expected_notification_id=notification_mock.id,
        expected_theme=texts.CLASSROOM_EVENT_REPETITION_UPDATED_V1_EMAIL_THEME,
        expected_pre_header=texts.CLASSROOM_EVENT_REPETITION_UPDATED_V1_EMAIL_PRE_HEADER,
        expected_header=texts.CLASSROOM_EVENT_REPETITION_UPDATED_V1_EMAIL_HEADER,
        expected_content=texts.CLASSROOM_EVENT_REPETITION_UPDATED_V1_EMAIL_CONTENT,
        expected_button_text=texts.CLASSROOM_SCHEDULE_FOCUS_BUTTON_TEXT,
        expected_button_link_path=f"/classrooms/{notification_payload.classroom_id}",
        expected_button_link_query={
            "tab": ["schedule"],
            "focused_at": [notification_payload.focused_at.isoformat()],
        },
    )


async def test_classroom_event_repetition_cancelled_v1_adapting(
    notification_mock: Mock,
) -> None:
    notification_payload: (
        notifications_sch.ClassroomScheduleFocusNotificationPayloadSchema
    ) = factories.ClassroomScheduleFocusNotificationPayloadFactory.build(
        kind=notifications_sch.NotificationKind.CLASSROOM_EVENT_REPETITION_CANCELLED_V1
    )
    notification_mock.payload = notification_payload

    email_notification_adapter = EmailNotificationAdapter(
        notification=notification_mock
    )

    result = email_notification_adapter.adapt()
    assert isinstance(result, pochta_sch.UniversalEmailMessagePayloadSchema)

    assert_universal_email_message_payload(
        result,
        expected_notification_id=notification_mock.id,
        expected_theme=texts.CLASSROOM_EVENT_REPETITION_CANCELLED_V1_EMAIL_THEME,
        expected_pre_header=texts.CLASSROOM_EVENT_REPETITION_CANCELLED_V1_EMAIL_PRE_HEADER,
        expected_header=texts.CLASSROOM_EVENT_REPETITION_CANCELLED_V1_EMAIL_HEADER,
        expected_content=texts.CLASSROOM_EVENT_REPETITION_CANCELLED_V1_EMAIL_CONTENT,
        expected_button_text=texts.CLASSROOM_SCHEDULE_FOCUS_BUTTON_TEXT,
        expected_button_link_path=f"/classrooms/{notification_payload.classroom_id}",
        expected_button_link_query={
            "tab": ["schedule"],
            "focused_at": [notification_payload.focused_at.isoformat()],
        },
    )


async def test_custom_v1_notification_adapting(
    notification_mock: Mock,
) -> None:
    notification_payload: notifications_sch.CustomNotificationPayloadSchema = (
        factories.CustomNotificationPayloadFactory.build(
            kind=notifications_sch.NotificationKind.CUSTOM_V1
        )
    )
    notification_mock.payload = notification_payload

    email_notification_adapter = EmailNotificationAdapter(
        notification=notification_mock
    )

    assert_contains(
        email_notification_adapter.adapt(),
        pochta_sch.CustomEmailMessagePayloadSchema(
            kind=pochta_sch.EmailMessageKind.CUSTOM_V1,
            theme=notification_payload.theme,
            pre_header=notification_payload.pre_header,
            header=notification_payload.header,
            content=notification_payload.content,
            button_text=notification_payload.button_text,
            button_link=notification_payload.button_link,
        ).model_dump(),
    )
