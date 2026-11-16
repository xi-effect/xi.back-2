from unittest.mock import Mock

import pytest

from app.common.schemas import notifications_sch
from app.notifications import texts
from app.notifications.services.notification_adapters.event_notification_adapters import (
    ClassroomEventInstanceCancelledV1NotificationAdapter,
    ClassroomEventInstanceRescheduledV1NotificationAdapter,
    ClassroomEventRepetitionCancelledV1NotificationAdapter,
    ClassroomEventRepetitionUpdatedV1NotificationAdapter,
    PersistedClassroomEventInstanceReminderV1NotificationAdapter,
    RepeatedClassroomEventInstanceReminderV1NotificationAdapter,
    RepeatingClassroomEventCreatedV1NotificationAdapter,
    SingleClassroomEventCreatedV1NotificationAdapter,
)
from tests.notifications import factories
from tests.notifications.utils import (
    assert_messenger_message_payload,
    assert_universal_email_message_payload,
)

pytestmark = pytest.mark.anyio


async def test_single_classroom_event_created_v1_messenger_adapting(
    notification_mock: Mock,
) -> None:
    notification_payload: (
        notifications_sch.PersistedClassroomEventInstanceNotificationPayloadSchema
    ) = factories.PersistedClassroomEventInstanceNotificationPayloadFactory.build(
        kind=notifications_sch.NotificationKind.SINGLE_CLASSROOM_EVENT_CREATED_V1,
    )

    notification_adapter = SingleClassroomEventCreatedV1NotificationAdapter(
        notification=notification_mock,
        payload=notification_payload,
    )

    assert_messenger_message_payload(
        notification_adapter.to_messenger_message_payload(),
        expected_notification_id=notification_mock.id,
        expected_message_text=texts.SINGLE_CLASSROOM_EVENT_CREATED_V1_MESSAGE,
        expected_button_text=texts.CLASSROOM_EVENT_INSTANCE_BUTTON_TEXT,
        expected_button_link_path=f"/classrooms/{notification_payload.classroom_id}",
        expected_button_link_query={
            "tab": ["schedule"],
            "event_instance_id": [str(notification_payload.event_instance_id)],
        },
    )


async def test_single_classroom_event_created_v1_email_adapting(
    notification_mock: Mock,
) -> None:
    notification_payload: (
        notifications_sch.PersistedClassroomEventInstanceNotificationPayloadSchema
    ) = factories.PersistedClassroomEventInstanceNotificationPayloadFactory.build(
        kind=notifications_sch.NotificationKind.SINGLE_CLASSROOM_EVENT_CREATED_V1,
    )

    notification_adapter = SingleClassroomEventCreatedV1NotificationAdapter(
        notification=notification_mock,
        payload=notification_payload,
    )

    assert_universal_email_message_payload(
        notification_adapter.to_universal_email_message_payload(),
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


async def test_classroom_event_instance_rescheduled_v1_messenger_adapting(
    notification_mock: Mock,
) -> None:
    notification_payload: (
        notifications_sch.PersistedClassroomEventInstanceNotificationPayloadSchema
    ) = factories.PersistedClassroomEventInstanceNotificationPayloadFactory.build(
        kind=notifications_sch.NotificationKind.CLASSROOM_EVENT_INSTANCE_RESCHEDULED_V1,
    )

    notification_adapter = ClassroomEventInstanceRescheduledV1NotificationAdapter(
        notification=notification_mock,
        payload=notification_payload,
    )

    assert_messenger_message_payload(
        notification_adapter.to_messenger_message_payload(),
        expected_notification_id=notification_mock.id,
        expected_message_text=texts.CLASSROOM_EVENT_INSTANCE_RESCHEDULED_V1_MESSAGE,
        expected_button_text=texts.CLASSROOM_EVENT_INSTANCE_BUTTON_TEXT,
        expected_button_link_path=f"/classrooms/{notification_payload.classroom_id}",
        expected_button_link_query={
            "tab": ["schedule"],
            "event_instance_id": [str(notification_payload.event_instance_id)],
        },
    )


async def test_classroom_event_instance_rescheduled_v1_email_adapting(
    notification_mock: Mock,
) -> None:
    notification_payload: (
        notifications_sch.PersistedClassroomEventInstanceNotificationPayloadSchema
    ) = factories.PersistedClassroomEventInstanceNotificationPayloadFactory.build(
        kind=notifications_sch.NotificationKind.CLASSROOM_EVENT_INSTANCE_RESCHEDULED_V1,
    )

    notification_adapter = ClassroomEventInstanceRescheduledV1NotificationAdapter(
        notification=notification_mock,
        payload=notification_payload,
    )

    assert_universal_email_message_payload(
        notification_adapter.to_universal_email_message_payload(),
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


async def test_classroom_event_instance_cancelled_v1_messenger_adapting(
    notification_mock: Mock,
) -> None:
    notification_payload: (
        notifications_sch.PersistedClassroomEventInstanceNotificationPayloadSchema
    ) = factories.PersistedClassroomEventInstanceNotificationPayloadFactory.build(
        kind=notifications_sch.NotificationKind.CLASSROOM_EVENT_INSTANCE_CANCELLED_V1,
    )

    notification_adapter = ClassroomEventInstanceCancelledV1NotificationAdapter(
        notification=notification_mock,
        payload=notification_payload,
    )

    assert_messenger_message_payload(
        notification_adapter.to_messenger_message_payload(),
        expected_notification_id=notification_mock.id,
        expected_message_text=texts.CLASSROOM_EVENT_INSTANCE_CANCELLED_V1_MESSAGE,
        expected_button_text=texts.CLASSROOM_EVENT_INSTANCE_BUTTON_TEXT,
        expected_button_link_path=f"/classrooms/{notification_payload.classroom_id}",
        expected_button_link_query={
            "tab": ["schedule"],
            "event_instance_id": [str(notification_payload.event_instance_id)],
        },
    )


async def test_classroom_event_instance_cancelled_v1_email_adapting(
    notification_mock: Mock,
) -> None:
    notification_payload: (
        notifications_sch.PersistedClassroomEventInstanceNotificationPayloadSchema
    ) = factories.PersistedClassroomEventInstanceNotificationPayloadFactory.build(
        kind=notifications_sch.NotificationKind.CLASSROOM_EVENT_INSTANCE_CANCELLED_V1,
    )

    notification_adapter = ClassroomEventInstanceCancelledV1NotificationAdapter(
        notification=notification_mock,
        payload=notification_payload,
    )

    assert_universal_email_message_payload(
        notification_adapter.to_universal_email_message_payload(),
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


async def test_persisted_classroom_event_instance_reminder_v1_messenger_adapting(
    notification_mock: Mock,
) -> None:
    notification_payload: (
        notifications_sch.PersistedClassroomEventInstanceNotificationPayloadSchema
    ) = factories.PersistedClassroomEventInstanceNotificationPayloadFactory.build(
        kind=notifications_sch.NotificationKind.PERSISTED_CLASSROOM_EVENT_INSTANCE_REMINDER_V1,
    )

    notification_adapter = PersistedClassroomEventInstanceReminderV1NotificationAdapter(
        notification=notification_mock,
        payload=notification_payload,
    )

    assert_messenger_message_payload(
        notification_adapter.to_messenger_message_payload(),
        expected_notification_id=notification_mock.id,
        expected_message_text=texts.CLASSROOM_EVENT_INSTANCE_REMINDER_V1_MESSAGE,
        expected_button_text=texts.CLASSROOM_EVENT_INSTANCE_BUTTON_TEXT,
        expected_button_link_path=f"/classrooms/{notification_payload.classroom_id}",
        expected_button_link_query={
            "tab": ["schedule"],
            "event_instance_id": [str(notification_payload.event_instance_id)],
        },
    )


async def test_persisted_classroom_event_instance_reminder_v1_email_adapting(
    notification_mock: Mock,
) -> None:
    notification_payload: (
        notifications_sch.PersistedClassroomEventInstanceNotificationPayloadSchema
    ) = factories.PersistedClassroomEventInstanceNotificationPayloadFactory.build(
        kind=notifications_sch.NotificationKind.PERSISTED_CLASSROOM_EVENT_INSTANCE_REMINDER_V1,
    )

    notification_adapter = PersistedClassroomEventInstanceReminderV1NotificationAdapter(
        notification=notification_mock,
        payload=notification_payload,
    )

    assert_universal_email_message_payload(
        notification_adapter.to_universal_email_message_payload(),
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


async def test_repeated_classroom_event_instance_reminder_v1_messenger_adapting(
    notification_mock: Mock,
) -> None:
    notification_payload: (
        notifications_sch.RepeatedClassroomEventInstanceNotificationPayloadSchema
    ) = factories.RepeatedClassroomEventInstanceNotificationPayloadFactory.build(
        kind=notifications_sch.NotificationKind.REPEATED_CLASSROOM_EVENT_INSTANCE_REMINDER_V1,
    )

    notification_adapter = RepeatedClassroomEventInstanceReminderV1NotificationAdapter(
        notification=notification_mock,
        payload=notification_payload,
    )

    assert_messenger_message_payload(
        notification_adapter.to_messenger_message_payload(),
        expected_notification_id=notification_mock.id,
        expected_message_text=texts.CLASSROOM_EVENT_INSTANCE_REMINDER_V1_MESSAGE,
        expected_button_text=texts.CLASSROOM_EVENT_INSTANCE_BUTTON_TEXT,
        expected_button_link_path=f"/classrooms/{notification_payload.classroom_id}",
        expected_button_link_query={
            "tab": ["schedule"],
            "repetition_mode_id": [str(notification_payload.repetition_mode_id)],
            "instance_index": [str(notification_payload.instance_index)],
        },
    )


async def test_repeated_classroom_event_instance_reminder_v1_email_adapting(
    notification_mock: Mock,
) -> None:
    notification_payload: (
        notifications_sch.RepeatedClassroomEventInstanceNotificationPayloadSchema
    ) = factories.RepeatedClassroomEventInstanceNotificationPayloadFactory.build(
        kind=notifications_sch.NotificationKind.REPEATED_CLASSROOM_EVENT_INSTANCE_REMINDER_V1,
    )

    notification_adapter = RepeatedClassroomEventInstanceReminderV1NotificationAdapter(
        notification=notification_mock,
        payload=notification_payload,
    )

    assert_universal_email_message_payload(
        notification_adapter.to_universal_email_message_payload(),
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


async def test_repeating_classroom_event_created_v1_messenger_adapting(
    notification_mock: Mock,
) -> None:
    notification_payload: (
        notifications_sch.ClassroomScheduleFocusNotificationPayloadSchema
    ) = factories.ClassroomScheduleFocusNotificationPayloadFactory.build(
        kind=notifications_sch.NotificationKind.REPEATING_CLASSROOM_EVENT_CREATED_V1,
    )

    notification_adapter = RepeatingClassroomEventCreatedV1NotificationAdapter(
        notification=notification_mock,
        payload=notification_payload,
    )

    assert_messenger_message_payload(
        notification_adapter.to_messenger_message_payload(),
        expected_notification_id=notification_mock.id,
        expected_message_text=texts.REPEATING_CLASSROOM_EVENT_CREATED_V1_MESSAGE,
        expected_button_text=texts.CLASSROOM_SCHEDULE_FOCUS_BUTTON_TEXT,
        expected_button_link_path=f"/classrooms/{notification_payload.classroom_id}",
        expected_button_link_query={
            "tab": ["schedule"],
            "focused_at": [notification_payload.focused_at.isoformat()],
        },
    )


async def test_repeating_classroom_event_created_v1_email_adapting(
    notification_mock: Mock,
) -> None:
    notification_payload: (
        notifications_sch.ClassroomScheduleFocusNotificationPayloadSchema
    ) = factories.ClassroomScheduleFocusNotificationPayloadFactory.build(
        kind=notifications_sch.NotificationKind.REPEATING_CLASSROOM_EVENT_CREATED_V1,
    )

    notification_adapter = RepeatingClassroomEventCreatedV1NotificationAdapter(
        notification=notification_mock,
        payload=notification_payload,
    )

    assert_universal_email_message_payload(
        notification_adapter.to_universal_email_message_payload(),
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


async def test_classroom_event_repetition_updated_v1_messenger_adapting(
    notification_mock: Mock,
) -> None:
    notification_payload: (
        notifications_sch.ClassroomScheduleFocusNotificationPayloadSchema
    ) = factories.ClassroomScheduleFocusNotificationPayloadFactory.build(
        kind=notifications_sch.NotificationKind.CLASSROOM_EVENT_REPETITION_UPDATED_V1,
    )

    notification_adapter = ClassroomEventRepetitionUpdatedV1NotificationAdapter(
        notification=notification_mock,
        payload=notification_payload,
    )

    assert_messenger_message_payload(
        notification_adapter.to_messenger_message_payload(),
        expected_notification_id=notification_mock.id,
        expected_message_text=texts.CLASSROOM_EVENT_REPETITION_UPDATED_V1_MESSAGE,
        expected_button_text=texts.CLASSROOM_SCHEDULE_FOCUS_BUTTON_TEXT,
        expected_button_link_path=f"/classrooms/{notification_payload.classroom_id}",
        expected_button_link_query={
            "tab": ["schedule"],
            "focused_at": [notification_payload.focused_at.isoformat()],
        },
    )


async def test_classroom_event_repetition_updated_v1_email_adapting(
    notification_mock: Mock,
) -> None:
    notification_payload: (
        notifications_sch.ClassroomScheduleFocusNotificationPayloadSchema
    ) = factories.ClassroomScheduleFocusNotificationPayloadFactory.build(
        kind=notifications_sch.NotificationKind.CLASSROOM_EVENT_REPETITION_UPDATED_V1,
    )

    notification_adapter = ClassroomEventRepetitionUpdatedV1NotificationAdapter(
        notification=notification_mock,
        payload=notification_payload,
    )

    assert_universal_email_message_payload(
        notification_adapter.to_universal_email_message_payload(),
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


async def test_classroom_event_repetition_cancelled_v1_messenger_adapting(
    notification_mock: Mock,
) -> None:
    notification_payload: (
        notifications_sch.ClassroomScheduleFocusNotificationPayloadSchema
    ) = factories.ClassroomScheduleFocusNotificationPayloadFactory.build(
        kind=notifications_sch.NotificationKind.CLASSROOM_EVENT_REPETITION_CANCELLED_V1,
    )

    notification_adapter = ClassroomEventRepetitionCancelledV1NotificationAdapter(
        notification=notification_mock,
        payload=notification_payload,
    )

    assert_messenger_message_payload(
        notification_adapter.to_messenger_message_payload(),
        expected_notification_id=notification_mock.id,
        expected_message_text=texts.CLASSROOM_EVENT_REPETITION_CANCELLED_V1_MESSAGE,
        expected_button_text=texts.CLASSROOM_SCHEDULE_FOCUS_BUTTON_TEXT,
        expected_button_link_path=f"/classrooms/{notification_payload.classroom_id}",
        expected_button_link_query={
            "tab": ["schedule"],
            "focused_at": [notification_payload.focused_at.isoformat()],
        },
    )


async def test_classroom_event_repetition_cancelled_v1_email_adapting(
    notification_mock: Mock,
) -> None:
    notification_payload: (
        notifications_sch.ClassroomScheduleFocusNotificationPayloadSchema
    ) = factories.ClassroomScheduleFocusNotificationPayloadFactory.build(
        kind=notifications_sch.NotificationKind.CLASSROOM_EVENT_REPETITION_CANCELLED_V1,
    )

    notification_adapter = ClassroomEventRepetitionCancelledV1NotificationAdapter(
        notification=notification_mock,
        payload=notification_payload,
    )

    assert_universal_email_message_payload(
        notification_adapter.to_universal_email_message_payload(),
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
