from app.common.schemas.notifications_sch import (
    ClassroomEventInstanceNotificationPayloadSchema,
    ClassroomNotificationPayloadSchema,
    ClassroomScheduleFocusNotificationPayloadSchema,
    CustomNotificationPayloadSchema,
    EnrollmentNotificationPayloadSchema,
    InvitationAcceptanceNotificationPayloadSchema,
    RecipientInvoiceNotificationPayloadSchema,
)
from app.common.schemas.pochta_sch import (
    AnyEmailMessagePayload,
    ClassroomNotificationEmailMessagePayloadSchema,
    CustomEmailMessagePayloadSchema,
    EmailMessageKind,
    RecipientInvoiceNotificationEmailMessagePayloadSchema,
    UniversalEmailMessagePayloadSchema,
)
from app.notifications import texts
from app.notifications.services.adapters.base_adapter import BaseNotificationAdapter


class NotificationToEmailMessageAdapter(
    BaseNotificationAdapter[AnyEmailMessagePayload]
):
    def adapt_individual_invitation_accepted_v1(
        self,
        payload: InvitationAcceptanceNotificationPayloadSchema,
    ) -> ClassroomNotificationEmailMessagePayloadSchema:
        return ClassroomNotificationEmailMessagePayloadSchema(
            kind=EmailMessageKind.INDIVIDUAL_INVITATION_ACCEPTED_V1,
            classroom_id=payload.classroom_id,
            notification_id=self.notification.id,
        )

    def adapt_group_invitation_accepted_v1(
        self,
        payload: InvitationAcceptanceNotificationPayloadSchema,
    ) -> ClassroomNotificationEmailMessagePayloadSchema:
        return ClassroomNotificationEmailMessagePayloadSchema(
            kind=EmailMessageKind.GROUP_INVITATION_ACCEPTED_V1,
            classroom_id=payload.classroom_id,
            notification_id=self.notification.id,
        )

    def adapt_enrollment_created_v1(
        self,
        payload: EnrollmentNotificationPayloadSchema,
    ) -> ClassroomNotificationEmailMessagePayloadSchema:
        return ClassroomNotificationEmailMessagePayloadSchema(
            kind=EmailMessageKind.ENROLLMENT_CREATED_V1,
            classroom_id=payload.classroom_id,
            notification_id=self.notification.id,
        )

    def adapt_classroom_conference_started_v1(
        self,
        payload: ClassroomNotificationPayloadSchema,
    ) -> ClassroomNotificationEmailMessagePayloadSchema:
        return ClassroomNotificationEmailMessagePayloadSchema(
            kind=EmailMessageKind.CLASSROOM_CONFERENCE_STARTED_V1,
            classroom_id=payload.classroom_id,
            notification_id=self.notification.id,
        )

    def adapt_recipient_invoice_created_v1(
        self,
        payload: RecipientInvoiceNotificationPayloadSchema,
    ) -> RecipientInvoiceNotificationEmailMessagePayloadSchema:
        return RecipientInvoiceNotificationEmailMessagePayloadSchema(
            kind=EmailMessageKind.RECIPIENT_INVOICE_CREATED_V1,
            recipient_invoice_id=payload.recipient_invoice_id,
            notification_id=self.notification.id,
        )

    def adapt_student_recipient_invoice_payment_confirmed_v1(
        self,
        payload: RecipientInvoiceNotificationPayloadSchema,
    ) -> RecipientInvoiceNotificationEmailMessagePayloadSchema:
        return RecipientInvoiceNotificationEmailMessagePayloadSchema(
            kind=EmailMessageKind.STUDENT_RECIPIENT_INVOICE_PAYMENT_CONFIRMED_V1,
            recipient_invoice_id=payload.recipient_invoice_id,
            notification_id=self.notification.id,
        )

    def adapt_single_classroom_event_created_v1(
        self, payload: ClassroomEventInstanceNotificationPayloadSchema
    ) -> UniversalEmailMessagePayloadSchema:
        return UniversalEmailMessagePayloadSchema(
            theme=texts.SINGLE_CLASSROOM_EVENT_CREATED_V1_EMAIL_THEME,
            pre_header=texts.SINGLE_CLASSROOM_EVENT_CREATED_V1_EMAIL_PRE_HEADER,
            header=texts.SINGLE_CLASSROOM_EVENT_CREATED_V1_EMAIL_HEADER,
            content=texts.SINGLE_CLASSROOM_EVENT_CREATED_V1_EMAIL_CONTENT,
            button_text=texts.CLASSROOM_EVENT_INSTANCE_BUTTON_TEXT,
            button_link=self.build_student_classroom_event_instance_url(payload),
        )

    def adapt_classroom_event_instance_rescheduled_v1(
        self, payload: ClassroomEventInstanceNotificationPayloadSchema
    ) -> UniversalEmailMessagePayloadSchema:
        return UniversalEmailMessagePayloadSchema(
            theme=texts.CLASSROOM_EVENT_INSTANCE_RESCHEDULED_V1_EMAIL_THEME,
            pre_header=texts.CLASSROOM_EVENT_INSTANCE_RESCHEDULED_V1_EMAIL_PRE_HEADER,
            header=texts.CLASSROOM_EVENT_INSTANCE_RESCHEDULED_V1_EMAIL_HEADER,
            content=texts.CLASSROOM_EVENT_INSTANCE_RESCHEDULED_V1_EMAIL_CONTENT,
            button_text=texts.CLASSROOM_EVENT_INSTANCE_BUTTON_TEXT,
            button_link=self.build_student_classroom_event_instance_url(payload),
        )

    def adapt_classroom_event_instance_cancelled_v1(
        self, payload: ClassroomEventInstanceNotificationPayloadSchema
    ) -> UniversalEmailMessagePayloadSchema:
        return UniversalEmailMessagePayloadSchema(
            theme=texts.CLASSROOM_EVENT_INSTANCE_CANCELLED_V1_EMAIL_THEME,
            pre_header=texts.CLASSROOM_EVENT_INSTANCE_CANCELLED_V1_EMAIL_PRE_HEADER,
            header=texts.CLASSROOM_EVENT_INSTANCE_CANCELLED_V1_EMAIL_HEADER,
            content=texts.CLASSROOM_EVENT_INSTANCE_CANCELLED_V1_EMAIL_CONTENT,
            button_text=texts.CLASSROOM_EVENT_INSTANCE_BUTTON_TEXT,
            button_link=self.build_student_classroom_event_instance_url(payload),
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
            button_link=self.build_student_classroom_schedule_focus_url(payload),
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
            button_link=self.build_student_classroom_schedule_focus_url(payload),
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
            button_link=self.build_student_classroom_schedule_focus_url(payload),
        )

    def adapt_custom_v1(
        self, payload: CustomNotificationPayloadSchema
    ) -> CustomEmailMessagePayloadSchema:
        return CustomEmailMessagePayloadSchema(
            kind=EmailMessageKind.CUSTOM_V1,
            theme=payload.theme,
            pre_header=payload.pre_header,
            header=payload.header,
            content=payload.content,
            button_text=payload.button_text,
            button_link=payload.button_link,
        )
