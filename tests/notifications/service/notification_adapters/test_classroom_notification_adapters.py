from unittest.mock import Mock

import pytest

from app.common.schemas import notifications_sch
from app.notifications import texts
from app.notifications.services.notification_adapters.classroom_notification_adapters import (
    ClassroomConferenceStartedV1NotificationAdapter,
    EnrollmentCreatedV1NotificationAdapter,
    GroupInvitationAcceptedV1NotificationAdapter,
    IndividualInvitationAcceptedV1NotificationAdapter,
)
from tests.notifications import factories
from tests.notifications.utils import (
    assert_messenger_message_payload,
    assert_universal_email_message_payload,
)

pytestmark = pytest.mark.anyio


async def test_individual_invitation_accepted_v1_messenger_adapting(
    notification_mock: Mock,
) -> None:
    notification_payload: (
        notifications_sch.InvitationAcceptanceNotificationPayloadSchema
    ) = factories.InvitationAcceptanceNotificationPayloadFactory.build(
        kind=notifications_sch.NotificationKind.INDIVIDUAL_INVITATION_ACCEPTED_V1,
    )

    notification_adapter = IndividualInvitationAcceptedV1NotificationAdapter(
        notification=notification_mock,
        payload=notification_payload,
    )

    assert_messenger_message_payload(
        notification_adapter.to_messenger_message_payload(),
        expected_notification_id=notification_mock.id,
        expected_message_text=texts.INDIVIDUAL_INVITATION_ACCEPTED_V1_MESSAGE,
        expected_button_text=texts.INDIVIDUAL_INVITATION_ACCEPTED_V1_BUTTON_TEXT,
        expected_button_link_path=f"/classrooms/{notification_payload.classroom_id}",
        expected_button_link_query={
            "tab": ["overview"],
            "role": ["tutor"],
        },
    )


async def test_individual_invitation_accepted_v1_email_adapting(
    notification_mock: Mock,
) -> None:
    notification_payload: (
        notifications_sch.InvitationAcceptanceNotificationPayloadSchema
    ) = factories.InvitationAcceptanceNotificationPayloadFactory.build(
        kind=notifications_sch.NotificationKind.INDIVIDUAL_INVITATION_ACCEPTED_V1,
    )

    notification_adapter = IndividualInvitationAcceptedV1NotificationAdapter(
        notification=notification_mock,
        payload=notification_payload,
    )

    assert_universal_email_message_payload(
        notification_adapter.to_universal_email_message_payload(),
        expected_notification_id=notification_mock.id,
        expected_theme=texts.INDIVIDUAL_INVITATION_ACCEPTED_V1_EMAIL_THEME,
        expected_pre_header=texts.INDIVIDUAL_INVITATION_ACCEPTED_V1_EMAIL_PRE_HEADER,
        expected_header=texts.INDIVIDUAL_INVITATION_ACCEPTED_V1_EMAIL_HEADER,
        expected_content=texts.INDIVIDUAL_INVITATION_ACCEPTED_V1_EMAIL_CONTENT,
        expected_button_text=texts.INDIVIDUAL_INVITATION_ACCEPTED_V1_BUTTON_TEXT,
        expected_button_link_path=f"/classrooms/{notification_payload.classroom_id}",
        expected_button_link_query={
            "tab": ["overview"],
            "role": ["tutor"],
        },
    )


async def test_group_invitation_accepted_v1_messenger_adapting(
    notification_mock: Mock,
) -> None:
    notification_payload: (
        notifications_sch.InvitationAcceptanceNotificationPayloadSchema
    ) = factories.InvitationAcceptanceNotificationPayloadFactory.build(
        kind=notifications_sch.NotificationKind.GROUP_INVITATION_ACCEPTED_V1,
    )

    notification_adapter = GroupInvitationAcceptedV1NotificationAdapter(
        notification=notification_mock,
        payload=notification_payload,
    )

    assert_messenger_message_payload(
        notification_adapter.to_messenger_message_payload(),
        expected_notification_id=notification_mock.id,
        expected_message_text=texts.GROUP_INVITATION_ACCEPTED_V1_MESSAGE,
        expected_button_text=texts.GROUP_INVITATION_ACCEPTED_V1_BUTTON_TEXT,
        expected_button_link_path=f"/classrooms/{notification_payload.classroom_id}",
        expected_button_link_query={
            "tab": ["overview"],
            "role": ["tutor"],
        },
    )


async def test_group_invitation_accepted_v1_email_adapting(
    notification_mock: Mock,
) -> None:
    notification_payload: (
        notifications_sch.InvitationAcceptanceNotificationPayloadSchema
    ) = factories.InvitationAcceptanceNotificationPayloadFactory.build(
        kind=notifications_sch.NotificationKind.GROUP_INVITATION_ACCEPTED_V1,
    )

    notification_adapter = GroupInvitationAcceptedV1NotificationAdapter(
        notification=notification_mock,
        payload=notification_payload,
    )

    assert_universal_email_message_payload(
        notification_adapter.to_universal_email_message_payload(),
        expected_notification_id=notification_mock.id,
        expected_theme=texts.GROUP_INVITATION_ACCEPTED_V1_EMAIL_THEME,
        expected_pre_header=texts.GROUP_INVITATION_ACCEPTED_V1_EMAIL_PRE_HEADER,
        expected_header=texts.GROUP_INVITATION_ACCEPTED_V1_EMAIL_HEADER,
        expected_content=texts.GROUP_INVITATION_ACCEPTED_V1_EMAIL_CONTENT,
        expected_button_text=texts.GROUP_INVITATION_ACCEPTED_V1_BUTTON_TEXT,
        expected_button_link_path=f"/classrooms/{notification_payload.classroom_id}",
        expected_button_link_query={
            "tab": ["overview"],
            "role": ["tutor"],
        },
    )


async def test_enrollment_created_v1_messenger_adapting(
    notification_mock: Mock,
) -> None:
    notification_payload: notifications_sch.EnrollmentNotificationPayloadSchema = (
        factories.EnrollmentNotificationPayloadFactory.build(
            kind=notifications_sch.NotificationKind.ENROLLMENT_CREATED_V1,
        )
    )

    notification_adapter = EnrollmentCreatedV1NotificationAdapter(
        notification=notification_mock,
        payload=notification_payload,
    )

    assert_messenger_message_payload(
        notification_adapter.to_messenger_message_payload(),
        expected_notification_id=notification_mock.id,
        expected_message_text=texts.ENROLLMENT_CREATED_V1_MESSAGE,
        expected_button_text=texts.ENROLLMENT_CREATED_V1_BUTTON_TEXT,
        expected_button_link_path=f"/classrooms/{notification_payload.classroom_id}",
        expected_button_link_query={
            "tab": ["overview"],
            "role": ["student"],
        },
    )


async def test_enrollment_created_v1_email_adapting(
    notification_mock: Mock,
) -> None:
    notification_payload: notifications_sch.EnrollmentNotificationPayloadSchema = (
        factories.EnrollmentNotificationPayloadFactory.build(
            kind=notifications_sch.NotificationKind.ENROLLMENT_CREATED_V1,
        )
    )

    notification_adapter = EnrollmentCreatedV1NotificationAdapter(
        notification=notification_mock,
        payload=notification_payload,
    )

    assert_universal_email_message_payload(
        notification_adapter.to_universal_email_message_payload(),
        expected_notification_id=notification_mock.id,
        expected_theme=texts.ENROLLMENT_CREATED_V1_EMAIL_THEME,
        expected_pre_header=texts.ENROLLMENT_CREATED_V1_EMAIL_PRE_HEADER,
        expected_header=texts.ENROLLMENT_CREATED_V1_EMAIL_HEADER,
        expected_content=texts.ENROLLMENT_CREATED_V1_EMAIL_CONTENT,
        expected_button_text=texts.ENROLLMENT_CREATED_V1_BUTTON_TEXT,
        expected_button_link_path=f"/classrooms/{notification_payload.classroom_id}",
        expected_button_link_query={
            "tab": ["overview"],
            "role": ["student"],
        },
    )


async def test_classroom_conference_started_v1_messenger_adapting(
    notification_mock: Mock,
) -> None:
    notification_payload: notifications_sch.ClassroomNotificationPayloadSchema = (
        factories.ClassroomNotificationPayloadFactory.build(
            kind=notifications_sch.NotificationKind.CLASSROOM_CONFERENCE_STARTED_V1,
        )
    )

    notification_adapter = ClassroomConferenceStartedV1NotificationAdapter(
        notification=notification_mock,
        payload=notification_payload,
    )

    assert_messenger_message_payload(
        notification_adapter.to_messenger_message_payload(),
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


async def test_classroom_conference_started_v1_email_adapting(
    notification_mock: Mock,
) -> None:
    notification_payload: notifications_sch.ClassroomNotificationPayloadSchema = (
        factories.ClassroomNotificationPayloadFactory.build(
            kind=notifications_sch.NotificationKind.CLASSROOM_CONFERENCE_STARTED_V1,
        )
    )

    notification_adapter = ClassroomConferenceStartedV1NotificationAdapter(
        notification=notification_mock,
        payload=notification_payload,
    )

    assert_universal_email_message_payload(
        notification_adapter.to_universal_email_message_payload(),
        expected_notification_id=notification_mock.id,
        expected_theme=texts.CLASSROOM_CONFERENCE_STARTED_V1_EMAIL_THEME,
        expected_pre_header=texts.CLASSROOM_CONFERENCE_STARTED_V1_EMAIL_PRE_HEADER,
        expected_header=texts.CLASSROOM_CONFERENCE_STARTED_V1_EMAIL_HEADER,
        expected_content=texts.CLASSROOM_CONFERENCE_STARTED_V1_EMAIL_CONTENT,
        expected_button_text=texts.CLASSROOM_CONFERENCE_STARTED_V1_BUTTON_TEXT,
        expected_button_link_path=f"/classrooms/{notification_payload.classroom_id}",
        expected_button_link_query={
            "tab": ["overview"],
            "role": ["student"],
            "goto": ["call"],
        },
    )
