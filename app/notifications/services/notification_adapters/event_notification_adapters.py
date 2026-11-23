from app.common.schemas.notifications_sch import (
    ClassroomScheduleFocusNotificationPayloadSchema,
    PersistedClassroomEventInstanceNotificationPayloadSchema,
    RepeatedClassroomEventInstanceNotificationPayloadSchema,
)
from app.notifications import texts
from app.notifications.services.notification_adapters.base_notification_adapter import (
    BaseNotificationAdapter,
)


class BasePersistedClassroomEventInstanceNotificationAdapter(
    BaseNotificationAdapter[PersistedClassroomEventInstanceNotificationPayloadSchema]
):
    def adapt_button_text(self) -> str:
        return texts.CLASSROOM_EVENT_INSTANCE_BUTTON_TEXT

    def adapt_button_link(self) -> str:
        return self.build_url(
            path=f"/classrooms/{self.payload.classroom_id}",
            params={
                "tab": "schedule",
                "event_instance_id": self.payload.event_instance_id,
            },
        )


class SingleClassroomEventCreatedV1NotificationAdapter(
    BasePersistedClassroomEventInstanceNotificationAdapter
):
    def adapt_message_text(self) -> str:
        return texts.SINGLE_CLASSROOM_EVENT_CREATED_V1_MESSAGE

    def adapt_email_theme(self) -> str:
        return texts.SINGLE_CLASSROOM_EVENT_CREATED_V1_EMAIL_THEME

    def adapt_email_pre_header(self) -> str:
        return texts.SINGLE_CLASSROOM_EVENT_CREATED_V1_EMAIL_PRE_HEADER

    def adapt_email_header(self) -> str:
        return texts.SINGLE_CLASSROOM_EVENT_CREATED_V1_EMAIL_HEADER

    def adapt_email_content(self) -> str:
        return texts.SINGLE_CLASSROOM_EVENT_CREATED_V1_EMAIL_CONTENT


class ClassroomEventInstanceRescheduledV1NotificationAdapter(
    BasePersistedClassroomEventInstanceNotificationAdapter
):
    def adapt_message_text(self) -> str:
        return texts.CLASSROOM_EVENT_INSTANCE_RESCHEDULED_V1_MESSAGE

    def adapt_email_theme(self) -> str:
        return texts.CLASSROOM_EVENT_INSTANCE_RESCHEDULED_V1_EMAIL_THEME

    def adapt_email_pre_header(self) -> str:
        return texts.CLASSROOM_EVENT_INSTANCE_RESCHEDULED_V1_EMAIL_PRE_HEADER

    def adapt_email_header(self) -> str:
        return texts.CLASSROOM_EVENT_INSTANCE_RESCHEDULED_V1_EMAIL_HEADER

    def adapt_email_content(self) -> str:
        return texts.CLASSROOM_EVENT_INSTANCE_RESCHEDULED_V1_EMAIL_CONTENT


class ClassroomEventInstanceCancelledV1NotificationAdapter(
    BasePersistedClassroomEventInstanceNotificationAdapter
):
    def adapt_message_text(self) -> str:
        return texts.CLASSROOM_EVENT_INSTANCE_CANCELLED_V1_MESSAGE

    def adapt_email_theme(self) -> str:
        return texts.CLASSROOM_EVENT_INSTANCE_CANCELLED_V1_EMAIL_THEME

    def adapt_email_pre_header(self) -> str:
        return texts.CLASSROOM_EVENT_INSTANCE_CANCELLED_V1_EMAIL_PRE_HEADER

    def adapt_email_header(self) -> str:
        return texts.CLASSROOM_EVENT_INSTANCE_CANCELLED_V1_EMAIL_HEADER

    def adapt_email_content(self) -> str:
        return texts.CLASSROOM_EVENT_INSTANCE_CANCELLED_V1_EMAIL_CONTENT


class PersistedClassroomEventInstanceReminderV1NotificationAdapter(
    BasePersistedClassroomEventInstanceNotificationAdapter
):
    def adapt_message_text(self) -> str:
        return texts.CLASSROOM_EVENT_INSTANCE_REMINDER_V1_MESSAGE

    def adapt_email_theme(self) -> str:
        return texts.CLASSROOM_EVENT_INSTANCE_REMINDER_V1_EMAIL_THEME

    def adapt_email_pre_header(self) -> str:
        return texts.CLASSROOM_EVENT_INSTANCE_REMINDER_V1_EMAIL_PRE_HEADER

    def adapt_email_header(self) -> str:
        return texts.CLASSROOM_EVENT_INSTANCE_REMINDER_V1_EMAIL_HEADER

    def adapt_email_content(self) -> str:
        return texts.CLASSROOM_EVENT_INSTANCE_REMINDER_V1_EMAIL_CONTENT


class RepeatedClassroomEventInstanceReminderV1NotificationAdapter(
    BaseNotificationAdapter[RepeatedClassroomEventInstanceNotificationPayloadSchema]
):
    def adapt_button_text(self) -> str:
        return texts.CLASSROOM_EVENT_INSTANCE_BUTTON_TEXT

    def adapt_button_link(self) -> str:
        return self.build_url(
            path=f"/classrooms/{self.payload.classroom_id}",
            params={
                "tab": "schedule",
                "repetition_mode_id": self.payload.repetition_mode_id,
                "instance_index": self.payload.instance_index,
            },
        )

    def adapt_message_text(self) -> str:
        return texts.CLASSROOM_EVENT_INSTANCE_REMINDER_V1_MESSAGE

    def adapt_email_theme(self) -> str:
        return texts.CLASSROOM_EVENT_INSTANCE_REMINDER_V1_EMAIL_THEME

    def adapt_email_pre_header(self) -> str:
        return texts.CLASSROOM_EVENT_INSTANCE_REMINDER_V1_EMAIL_PRE_HEADER

    def adapt_email_header(self) -> str:
        return texts.CLASSROOM_EVENT_INSTANCE_REMINDER_V1_EMAIL_HEADER

    def adapt_email_content(self) -> str:
        return texts.CLASSROOM_EVENT_INSTANCE_REMINDER_V1_EMAIL_CONTENT


class BaseClassroomScheduleFocusNotificationAdapter(
    BaseNotificationAdapter[ClassroomScheduleFocusNotificationPayloadSchema]
):
    def adapt_button_text(self) -> str:
        return texts.CLASSROOM_SCHEDULE_FOCUS_BUTTON_TEXT

    def adapt_button_link(self) -> str:
        return self.build_url(
            path=f"/classrooms/{self.payload.classroom_id}",
            params={
                "tab": "schedule",
                "focused_at": self.payload.focused_at.isoformat(),
            },
        )


class RepeatingClassroomEventCreatedV1NotificationAdapter(
    BaseClassroomScheduleFocusNotificationAdapter
):
    def adapt_message_text(self) -> str:
        return texts.REPEATING_CLASSROOM_EVENT_CREATED_V1_MESSAGE

    def adapt_email_theme(self) -> str:
        return texts.REPEATING_CLASSROOM_EVENT_CREATED_V1_EMAIL_THEME

    def adapt_email_pre_header(self) -> str:
        return texts.REPEATING_CLASSROOM_EVENT_CREATED_V1_EMAIL_PRE_HEADER

    def adapt_email_header(self) -> str:
        return texts.REPEATING_CLASSROOM_EVENT_CREATED_V1_EMAIL_HEADER

    def adapt_email_content(self) -> str:
        return texts.REPEATING_CLASSROOM_EVENT_CREATED_V1_EMAIL_CONTENT


class ClassroomEventRepetitionUpdatedV1NotificationAdapter(
    BaseClassroomScheduleFocusNotificationAdapter
):
    def adapt_message_text(self) -> str:
        return texts.CLASSROOM_EVENT_REPETITION_UPDATED_V1_MESSAGE

    def adapt_email_theme(self) -> str:
        return texts.CLASSROOM_EVENT_REPETITION_UPDATED_V1_EMAIL_THEME

    def adapt_email_pre_header(self) -> str:
        return texts.CLASSROOM_EVENT_REPETITION_UPDATED_V1_EMAIL_PRE_HEADER

    def adapt_email_header(self) -> str:
        return texts.CLASSROOM_EVENT_REPETITION_UPDATED_V1_EMAIL_HEADER

    def adapt_email_content(self) -> str:
        return texts.CLASSROOM_EVENT_REPETITION_UPDATED_V1_EMAIL_CONTENT


class ClassroomEventRepetitionCancelledV1NotificationAdapter(
    BaseClassroomScheduleFocusNotificationAdapter
):
    def adapt_message_text(self) -> str:
        return texts.CLASSROOM_EVENT_REPETITION_CANCELLED_V1_MESSAGE

    def adapt_email_theme(self) -> str:
        return texts.CLASSROOM_EVENT_REPETITION_CANCELLED_V1_EMAIL_THEME

    def adapt_email_pre_header(self) -> str:
        return texts.CLASSROOM_EVENT_REPETITION_CANCELLED_V1_EMAIL_PRE_HEADER

    def adapt_email_header(self) -> str:
        return texts.CLASSROOM_EVENT_REPETITION_CANCELLED_V1_EMAIL_HEADER

    def adapt_email_content(self) -> str:
        return texts.CLASSROOM_EVENT_REPETITION_CANCELLED_V1_EMAIL_CONTENT
