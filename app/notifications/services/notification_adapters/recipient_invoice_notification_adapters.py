from app.common.schemas.classrooms_sch import ClassroomRole
from app.common.schemas.notifications_sch import (
    RecipientInvoiceNotificationPayloadSchema,
)
from app.notifications import texts
from app.notifications.services.notification_adapters.base_notification_adapter import (
    BaseNotificationAdapter,
)


class BaseRecipientInvoiceNotificationAdapter(
    BaseNotificationAdapter[RecipientInvoiceNotificationPayloadSchema]
):
    def build_recipient_invoice_url(self, role: ClassroomRole) -> str:
        return self.build_url(
            path="/payments",
            params={
                "tab": "invoices",
                "role": role,
                "recipient_invoice_id": self.payload.recipient_invoice_id,
            },
        )


class RecipientInvoiceCreatedV1NotificationAdapter(
    BaseRecipientInvoiceNotificationAdapter
):
    def adapt_button_text(self) -> str:
        return texts.RECIPIENT_INVOICE_CREATED_V1_BUTTON_TEXT

    def adapt_button_link(self) -> str:
        return self.build_recipient_invoice_url(ClassroomRole.STUDENT)

    def adapt_message_text(self) -> str:
        return texts.RECIPIENT_INVOICE_CREATED_V1_MESSAGE

    def adapt_email_theme(self) -> str:
        return texts.RECIPIENT_INVOICE_CREATED_V1_EMAIL_THEME

    def adapt_email_pre_header(self) -> str:
        return texts.RECIPIENT_INVOICE_CREATED_V1_EMAIL_PRE_HEADER

    def adapt_email_header(self) -> str:
        return texts.RECIPIENT_INVOICE_CREATED_V1_EMAIL_HEADER

    def adapt_email_content(self) -> str:
        return texts.RECIPIENT_INVOICE_CREATED_V1_EMAIL_CONTENT


class StudentRecipientInvoicePaymentConfirmedV1NotificationAdapter(
    BaseRecipientInvoiceNotificationAdapter
):
    def adapt_button_text(self) -> str:
        return texts.STUDENT_RECIPIENT_INVOICE_PAYMENT_CONFIRMED_V1_BUTTON_TEXT

    def adapt_button_link(self) -> str:
        return self.build_recipient_invoice_url(ClassroomRole.TUTOR)

    def adapt_message_text(self) -> str:
        return texts.STUDENT_RECIPIENT_INVOICE_PAYMENT_CONFIRMED_V1_MESSAGE

    def adapt_email_theme(self) -> str:
        return texts.STUDENT_RECIPIENT_INVOICE_PAYMENT_CONFIRMED_V1_EMAIL_THEME

    def adapt_email_pre_header(self) -> str:
        return texts.STUDENT_RECIPIENT_INVOICE_PAYMENT_CONFIRMED_V1_EMAIL_PRE_HEADER

    def adapt_email_header(self) -> str:
        return texts.STUDENT_RECIPIENT_INVOICE_PAYMENT_CONFIRMED_V1_EMAIL_HEADER

    def adapt_email_content(self) -> str:
        return texts.STUDENT_RECIPIENT_INVOICE_PAYMENT_CONFIRMED_V1_EMAIL_CONTENT
