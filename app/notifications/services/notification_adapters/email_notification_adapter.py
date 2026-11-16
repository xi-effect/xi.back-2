from app.common.schemas.classrooms_sch import ClassroomRole
from app.common.schemas.notifications_sch import (
    ClassroomNotificationPayloadSchema,
    ClassroomScheduleFocusNotificationPayloadSchema,
    CustomNotificationPayloadSchema,
    EnrollmentNotificationPayloadSchema,
    InvitationAcceptanceNotificationPayloadSchema,
    PersistedClassroomEventInstanceNotificationPayloadSchema,
    RecipientInvoiceNotificationPayloadSchema,
    RepeatedClassroomEventInstanceNotificationPayloadSchema,
)
from app.common.schemas.pochta_sch import UniversalEmailMessagePayloadSchema
from app.notifications import texts
from app.notifications.services.notification_adapters.base_notification_adapter import (
    BaseNotificationAdapter,
)


class EmailNotificationAdapter(
    BaseNotificationAdapter[UniversalEmailMessagePayloadSchema]
):
    def adapt_individual_invitation_accepted_v1(
        self,
        payload: InvitationAcceptanceNotificationPayloadSchema,
    ) -> UniversalEmailMessagePayloadSchema:
        return UniversalEmailMessagePayloadSchema(
            theme=texts.INDIVIDUAL_INVITATION_ACCEPTED_V1_EMAIL_THEME,
            pre_header=texts.INDIVIDUAL_INVITATION_ACCEPTED_V1_EMAIL_PRE_HEADER,
            header=texts.INDIVIDUAL_INVITATION_ACCEPTED_V1_EMAIL_HEADER,
            content=texts.INDIVIDUAL_INVITATION_ACCEPTED_V1_EMAIL_CONTENT,
            button_text=texts.INDIVIDUAL_INVITATION_ACCEPTED_V1_EMAIL_BUTTON_TEXT,
            button_link=self.build_classroom_overview_url(
                payload.classroom_id,
                ClassroomRole.TUTOR,
            ),
        )

    def adapt_group_invitation_accepted_v1(
        self,
        payload: InvitationAcceptanceNotificationPayloadSchema,
    ) -> UniversalEmailMessagePayloadSchema:
        return UniversalEmailMessagePayloadSchema(
            theme=texts.GROUP_INVITATION_ACCEPTED_V1_EMAIL_THEME,
            pre_header=texts.GROUP_INVITATION_ACCEPTED_V1_EMAIL_PRE_HEADER,
            header=texts.GROUP_INVITATION_ACCEPTED_V1_EMAIL_HEADER,
            content=texts.GROUP_INVITATION_ACCEPTED_V1_EMAIL_CONTENT,
            button_text=texts.GROUP_INVITATION_ACCEPTED_V1_BUTTON_TEXT,
            button_link=self.build_classroom_overview_url(
                payload.classroom_id,
                ClassroomRole.TUTOR,
            ),
        )

    def adapt_enrollment_created_v1(
        self,
        payload: EnrollmentNotificationPayloadSchema,
    ) -> UniversalEmailMessagePayloadSchema:
        return UniversalEmailMessagePayloadSchema(
            theme=texts.ENROLLMENT_CREATED_V1_EMAIL_THEME,
            pre_header=texts.ENROLLMENT_CREATED_V1_EMAIL_PRE_HEADER,
            header=texts.ENROLLMENT_CREATED_V1_EMAIL_HEADER,
            content=texts.ENROLLMENT_CREATED_V1_EMAIL_CONTENT,
            button_text=texts.ENROLLMENT_CREATED_V1_BUTTON_TEXT,
            button_link=self.build_classroom_overview_url(
                payload.classroom_id,
                ClassroomRole.STUDENT,
            ),
        )

    def adapt_classroom_conference_started_v1(
        self,
        payload: ClassroomNotificationPayloadSchema,
    ) -> UniversalEmailMessagePayloadSchema:
        return UniversalEmailMessagePayloadSchema(
            theme=texts.CLASSROOM_CONFERENCE_STARTED_V1_EMAIL_THEME,
            pre_header=texts.CLASSROOM_CONFERENCE_STARTED_V1_EMAIL_PRE_HEADER,
            header=texts.CLASSROOM_CONFERENCE_STARTED_V1_EMAIL_HEADER,
            content=texts.CLASSROOM_CONFERENCE_STARTED_V1_EMAIL_CONTENT,
            button_text=texts.CLASSROOM_CONFERENCE_STARTED_V1_BUTTON_TEXT,
            button_link=self.build_classroom_conference_url(payload),
        )

    def adapt_recipient_invoice_created_v1(
        self,
        payload: RecipientInvoiceNotificationPayloadSchema,
    ) -> UniversalEmailMessagePayloadSchema:
        return UniversalEmailMessagePayloadSchema(
            theme=texts.RECIPIENT_INVOICE_CREATED_V1_EMAIL_THEME,
            pre_header=texts.RECIPIENT_INVOICE_CREATED_V1_EMAIL_PRE_HEADER,
            header=texts.RECIPIENT_INVOICE_CREATED_V1_EMAIL_HEADER,
            content=texts.RECIPIENT_INVOICE_CREATED_V1_EMAIL_CONTENT,
            button_text=texts.RECIPIENT_INVOICE_CREATED_V1_BUTTON_TEXT,
            button_link=self.build_recipient_invoice_url(
                payload,
                ClassroomRole.STUDENT,
            ),
        )

    def adapt_student_recipient_invoice_payment_confirmed_v1(
        self,
        payload: RecipientInvoiceNotificationPayloadSchema,
    ) -> UniversalEmailMessagePayloadSchema:
        return UniversalEmailMessagePayloadSchema(
            theme=texts.STUDENT_RECIPIENT_INVOICE_PAYMENT_CONFIRMED_V1_EMAIL_THEME,
            pre_header=texts.STUDENT_RECIPIENT_INVOICE_PAYMENT_CONFIRMED_V1_EMAIL_PRE_HEADER,
            header=texts.STUDENT_RECIPIENT_INVOICE_PAYMENT_CONFIRMED_V1_EMAIL_HEADER,
            content=texts.STUDENT_RECIPIENT_INVOICE_PAYMENT_CONFIRMED_V1_EMAIL_CONTENT,
            button_text=texts.STUDENT_RECIPIENT_INVOICE_PAYMENT_CONFIRMED_V1_EMAIL_BUTTON_TEXT,
            button_link=self.build_recipient_invoice_url(payload, ClassroomRole.TUTOR),
        )

    def adapt_single_classroom_event_created_v1(
        self, payload: PersistedClassroomEventInstanceNotificationPayloadSchema
    ) -> UniversalEmailMessagePayloadSchema:
        return UniversalEmailMessagePayloadSchema(
            theme=texts.SINGLE_CLASSROOM_EVENT_CREATED_V1_EMAIL_THEME,
            pre_header=texts.SINGLE_CLASSROOM_EVENT_CREATED_V1_EMAIL_PRE_HEADER,
            header=texts.SINGLE_CLASSROOM_EVENT_CREATED_V1_EMAIL_HEADER,
            content=texts.SINGLE_CLASSROOM_EVENT_CREATED_V1_EMAIL_CONTENT,
            button_text=texts.CLASSROOM_EVENT_INSTANCE_BUTTON_TEXT,
            button_link=self.build_persisted_classroom_event_instance_url(payload),
        )

    def adapt_classroom_event_instance_rescheduled_v1(
        self, payload: PersistedClassroomEventInstanceNotificationPayloadSchema
    ) -> UniversalEmailMessagePayloadSchema:
        return UniversalEmailMessagePayloadSchema(
            theme=texts.CLASSROOM_EVENT_INSTANCE_RESCHEDULED_V1_EMAIL_THEME,
            pre_header=texts.CLASSROOM_EVENT_INSTANCE_RESCHEDULED_V1_EMAIL_PRE_HEADER,
            header=texts.CLASSROOM_EVENT_INSTANCE_RESCHEDULED_V1_EMAIL_HEADER,
            content=texts.CLASSROOM_EVENT_INSTANCE_RESCHEDULED_V1_EMAIL_CONTENT,
            button_text=texts.CLASSROOM_EVENT_INSTANCE_BUTTON_TEXT,
            button_link=self.build_persisted_classroom_event_instance_url(payload),
        )

    def adapt_classroom_event_instance_cancelled_v1(
        self, payload: PersistedClassroomEventInstanceNotificationPayloadSchema
    ) -> UniversalEmailMessagePayloadSchema:
        return UniversalEmailMessagePayloadSchema(
            theme=texts.CLASSROOM_EVENT_INSTANCE_CANCELLED_V1_EMAIL_THEME,
            pre_header=texts.CLASSROOM_EVENT_INSTANCE_CANCELLED_V1_EMAIL_PRE_HEADER,
            header=texts.CLASSROOM_EVENT_INSTANCE_CANCELLED_V1_EMAIL_HEADER,
            content=texts.CLASSROOM_EVENT_INSTANCE_CANCELLED_V1_EMAIL_CONTENT,
            button_text=texts.CLASSROOM_EVENT_INSTANCE_BUTTON_TEXT,
            button_link=self.build_persisted_classroom_event_instance_url(payload),
        )

    def adapt_persisted_classroom_event_instance_reminder_v1(
        self,
        payload: PersistedClassroomEventInstanceNotificationPayloadSchema,
    ) -> UniversalEmailMessagePayloadSchema:
        return UniversalEmailMessagePayloadSchema(
            theme=texts.CLASSROOM_EVENT_INSTANCE_REMINDER_V1_EMAIL_THEME,
            pre_header=texts.CLASSROOM_EVENT_INSTANCE_REMINDER_V1_EMAIL_PRE_HEADER,
            header=texts.CLASSROOM_EVENT_INSTANCE_REMINDER_V1_EMAIL_HEADER,
            content=texts.CLASSROOM_EVENT_INSTANCE_REMINDER_V1_EMAIL_CONTENT,
            button_text=texts.CLASSROOM_EVENT_INSTANCE_BUTTON_TEXT,
            button_link=self.build_persisted_classroom_event_instance_url(payload),
        )

    def adapt_repeated_classroom_event_instance_reminder_v1(
        self,
        payload: RepeatedClassroomEventInstanceNotificationPayloadSchema,
    ) -> UniversalEmailMessagePayloadSchema:
        return UniversalEmailMessagePayloadSchema(
            theme=texts.CLASSROOM_EVENT_INSTANCE_REMINDER_V1_EMAIL_THEME,
            pre_header=texts.CLASSROOM_EVENT_INSTANCE_REMINDER_V1_EMAIL_PRE_HEADER,
            header=texts.CLASSROOM_EVENT_INSTANCE_REMINDER_V1_EMAIL_HEADER,
            content=texts.CLASSROOM_EVENT_INSTANCE_REMINDER_V1_EMAIL_CONTENT,
            button_text=texts.CLASSROOM_EVENT_INSTANCE_BUTTON_TEXT,
            button_link=self.build_repeated_classroom_event_instance_url(payload),
        )

    def adapt_repeating_classroom_event_created_v1(
        self, payload: ClassroomScheduleFocusNotificationPayloadSchema
    ) -> UniversalEmailMessagePayloadSchema:
        return UniversalEmailMessagePayloadSchema(
            theme=texts.REPEATING_CLASSROOM_EVENT_CREATED_V1_EMAIL_THEME,
            pre_header=texts.REPEATING_CLASSROOM_EVENT_CREATED_V1_EMAIL_PRE_HEADER,
            header=texts.REPEATING_CLASSROOM_EVENT_CREATED_V1_EMAIL_HEADER,
            content=texts.REPEATING_CLASSROOM_EVENT_CREATED_V1_EMAIL_CONTENT,
            button_text=texts.CLASSROOM_SCHEDULE_FOCUS_BUTTON_TEXT,
            button_link=self.build_classroom_schedule_focus_url(payload),
        )

    def adapt_classroom_event_repetition_updated_v1(
        self, payload: ClassroomScheduleFocusNotificationPayloadSchema
    ) -> UniversalEmailMessagePayloadSchema:
        return UniversalEmailMessagePayloadSchema(
            theme=texts.CLASSROOM_EVENT_REPETITION_UPDATED_V1_EMAIL_THEME,
            pre_header=texts.CLASSROOM_EVENT_REPETITION_UPDATED_V1_EMAIL_PRE_HEADER,
            header=texts.CLASSROOM_EVENT_REPETITION_UPDATED_V1_EMAIL_HEADER,
            content=texts.CLASSROOM_EVENT_REPETITION_UPDATED_V1_EMAIL_CONTENT,
            button_text=texts.CLASSROOM_SCHEDULE_FOCUS_BUTTON_TEXT,
            button_link=self.build_classroom_schedule_focus_url(payload),
        )

    def adapt_classroom_event_repetition_cancelled_v1(
        self, payload: ClassroomScheduleFocusNotificationPayloadSchema
    ) -> UniversalEmailMessagePayloadSchema:
        return UniversalEmailMessagePayloadSchema(
            theme=texts.CLASSROOM_EVENT_REPETITION_CANCELLED_V1_EMAIL_THEME,
            pre_header=texts.CLASSROOM_EVENT_REPETITION_CANCELLED_V1_EMAIL_PRE_HEADER,
            header=texts.CLASSROOM_EVENT_REPETITION_CANCELLED_V1_EMAIL_HEADER,
            content=texts.CLASSROOM_EVENT_REPETITION_CANCELLED_V1_EMAIL_CONTENT,
            button_text=texts.CLASSROOM_SCHEDULE_FOCUS_BUTTON_TEXT,
            button_link=self.build_classroom_schedule_focus_url(payload),
        )

    def adapt_custom_v1(
        self, payload: CustomNotificationPayloadSchema
    ) -> UniversalEmailMessagePayloadSchema:
        return UniversalEmailMessagePayloadSchema(
            theme=payload.theme,
            pre_header=payload.pre_header,
            header=payload.header,
            content=payload.content,
            button_text=payload.button_text,
            button_link=payload.button_link,
        )
