from app.common.schemas.notifications_sch import (
    ClassroomNotificationPayloadSchema,
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
)
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
