from pydantic import BaseModel

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
from app.notifications import texts
from app.notifications.services.adapters.base_adapter import BaseNotificationAdapter


class MessengerMessagePayloadSchema(BaseModel):
    message_text: str
    button_text: str
    button_link: str


class MessengerNotificationAdapter(
    BaseNotificationAdapter[MessengerMessagePayloadSchema]
):
    def adapt_individual_invitation_accepted_v1(
        self,
        payload: InvitationAcceptanceNotificationPayloadSchema,
    ) -> MessengerMessagePayloadSchema:
        return MessengerMessagePayloadSchema(
            message_text=texts.INDIVIDUAL_INVITATION_ACCEPTED_V1_MESSAGE,
            button_text=texts.INDIVIDUAL_INVITATION_ACCEPTED_V1_BUTTON_TEXT,
            button_link=self.build_url(
                path=f"/classrooms/{payload.classroom_id}",
                params={"tab": "overview", "role": "tutor"},
            ),
        )

    def adapt_group_invitation_accepted_v1(
        self,
        payload: InvitationAcceptanceNotificationPayloadSchema,
    ) -> MessengerMessagePayloadSchema:
        return MessengerMessagePayloadSchema(
            message_text=texts.GROUP_INVITATION_ACCEPTED_V1_MESSAGE,
            button_text=texts.GROUP_INVITATION_ACCEPTED_V1_BUTTON_TEXT,
            button_link=self.build_url(
                path=f"/classrooms/{payload.classroom_id}",
                params={"tab": "overview", "role": "tutor"},
            ),
        )

    def adapt_enrollment_created_v1(
        self,
        payload: EnrollmentNotificationPayloadSchema,
    ) -> MessengerMessagePayloadSchema:
        return MessengerMessagePayloadSchema(
            message_text=texts.ENROLLMENT_CREATED_V1_MESSAGE,
            button_text=texts.ENROLLMENT_CREATED_V1_BUTTON_TEXT,
            button_link=self.build_url(
                path=f"/classrooms/{payload.classroom_id}",
                params={"tab": "overview", "role": "student"},
            ),
        )

    def adapt_classroom_conference_started_v1(
        self,
        payload: ClassroomNotificationPayloadSchema,
    ) -> MessengerMessagePayloadSchema:
        return MessengerMessagePayloadSchema(
            message_text=texts.CLASSROOM_CONFERENCE_STARTED_V1_MESSAGE,
            button_text=texts.CLASSROOM_CONFERENCE_STARTED_V1_BUTTON_TEXT,
            button_link=self.build_url(
                path=f"/classrooms/{payload.classroom_id}",
                params={"tab": "overview", "role": "student", "goto": "call"},
            ),
        )

    def adapt_recipient_invoice_created_v1(
        self,
        payload: RecipientInvoiceNotificationPayloadSchema,
    ) -> MessengerMessagePayloadSchema:
        return MessengerMessagePayloadSchema(
            message_text=texts.RECIPIENT_INVOICE_CREATED_V1_MESSAGE,
            button_text=texts.RECIPIENT_INVOICE_CREATED_V1_BUTTON_TEXT,
            button_link=self.build_url(
                path="/payments",
                params={
                    "tab": "invoices",
                    "role": "student",
                    "recipient_invoice_id": payload.recipient_invoice_id,
                },
            ),
        )

    def adapt_student_recipient_invoice_payment_confirmed_v1(
        self,
        payload: RecipientInvoiceNotificationPayloadSchema,
    ) -> MessengerMessagePayloadSchema:
        return MessengerMessagePayloadSchema(
            message_text=texts.STUDENT_RECIPIENT_INVOICE_PAYMENT_CONFIRMED_V1_MESSAGE,
            button_text=texts.STUDENT_RECIPIENT_INVOICE_PAYMENT_CONFIRMED_V1_BUTTON_TEXT,
            button_link=self.build_url(
                path="/payments",
                params={
                    "tab": "invoices",
                    "role": "tutor",
                    "recipient_invoice_id": payload.recipient_invoice_id,
                },
            ),
        )

    def adapt_single_classroom_event_created_v1(
        self, payload: PersistedClassroomEventInstanceNotificationPayloadSchema
    ) -> MessengerMessagePayloadSchema:
        return MessengerMessagePayloadSchema(
            message_text=texts.SINGLE_CLASSROOM_EVENT_CREATED_V1_MESSAGE,
            button_text=texts.CLASSROOM_EVENT_INSTANCE_BUTTON_TEXT,
            button_link=self.build_persisted_classroom_event_instance_url(payload),
        )

    def adapt_classroom_event_instance_rescheduled_v1(
        self, payload: PersistedClassroomEventInstanceNotificationPayloadSchema
    ) -> MessengerMessagePayloadSchema:
        return MessengerMessagePayloadSchema(
            message_text=texts.CLASSROOM_EVENT_INSTANCE_RESCHEDULED_V1_MESSAGE,
            button_text=texts.CLASSROOM_EVENT_INSTANCE_BUTTON_TEXT,
            button_link=self.build_persisted_classroom_event_instance_url(payload),
        )

    def adapt_classroom_event_instance_cancelled_v1(
        self, payload: PersistedClassroomEventInstanceNotificationPayloadSchema
    ) -> MessengerMessagePayloadSchema:
        return MessengerMessagePayloadSchema(
            message_text=texts.CLASSROOM_EVENT_INSTANCE_CANCELLED_V1_MESSAGE,
            button_text=texts.CLASSROOM_EVENT_INSTANCE_BUTTON_TEXT,
            button_link=self.build_persisted_classroom_event_instance_url(payload),
        )

    def adapt_persisted_classroom_event_instance_reminder_v1(
        self,
        payload: PersistedClassroomEventInstanceNotificationPayloadSchema,
    ) -> MessengerMessagePayloadSchema:
        return MessengerMessagePayloadSchema(
            message_text=texts.CLASSROOM_EVENT_INSTANCE_REMINDER_V1_MESSAGE,
            button_text=texts.CLASSROOM_EVENT_INSTANCE_BUTTON_TEXT,
            button_link=self.build_persisted_classroom_event_instance_url(payload),
        )

    def adapt_repeated_classroom_event_instance_reminder_v1(
        self,
        payload: RepeatedClassroomEventInstanceNotificationPayloadSchema,
    ) -> MessengerMessagePayloadSchema:
        return MessengerMessagePayloadSchema(
            message_text=texts.CLASSROOM_EVENT_INSTANCE_REMINDER_V1_MESSAGE,
            button_text=texts.CLASSROOM_EVENT_INSTANCE_BUTTON_TEXT,
            button_link=self.build_repeated_classroom_event_instance_url(payload),
        )

    def adapt_repeating_classroom_event_created_v1(
        self, payload: ClassroomScheduleFocusNotificationPayloadSchema
    ) -> MessengerMessagePayloadSchema:
        return MessengerMessagePayloadSchema(
            message_text=texts.REPEATING_CLASSROOM_EVENT_CREATED_V1_MESSAGE,
            button_text=texts.CLASSROOM_SCHEDULE_FOCUS_BUTTON_TEXT,
            button_link=self.build_classroom_schedule_focus_url(payload),
        )

    def adapt_classroom_event_repetition_updated_v1(
        self, payload: ClassroomScheduleFocusNotificationPayloadSchema
    ) -> MessengerMessagePayloadSchema:
        return MessengerMessagePayloadSchema(
            message_text=texts.CLASSROOM_EVENT_REPETITION_UPDATED_V1_MESSAGE,
            button_text=texts.CLASSROOM_SCHEDULE_FOCUS_BUTTON_TEXT,
            button_link=self.build_classroom_schedule_focus_url(payload),
        )

    def adapt_classroom_event_repetition_cancelled_v1(
        self, payload: ClassroomScheduleFocusNotificationPayloadSchema
    ) -> MessengerMessagePayloadSchema:
        return MessengerMessagePayloadSchema(
            message_text=texts.CLASSROOM_EVENT_REPETITION_CANCELLED_V1_MESSAGE,
            button_text=texts.CLASSROOM_SCHEDULE_FOCUS_BUTTON_TEXT,
            button_link=self.build_classroom_schedule_focus_url(payload),
        )

    def adapt_custom_v1(
        self,
        payload: CustomNotificationPayloadSchema,
    ) -> MessengerMessagePayloadSchema:
        return MessengerMessagePayloadSchema(
            message_text=f"{payload.header}\n\n{payload.content}",
            button_text=payload.button_text,
            button_link=payload.button_link,
        )
