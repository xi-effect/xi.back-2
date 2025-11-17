from typing import Any
from urllib.parse import urlencode

from pydantic import BaseModel

from app.common.config import settings
from app.common.schemas.notifications_sch import (
    ClassroomNotificationPayloadSchema,
    EnrollmentNotificationPayloadSchema,
    InvitationAcceptanceNotificationPayloadSchema,
    RecipientInvoiceNotificationPayloadSchema,
)
from app.notifications import texts
from app.notifications.services.adapters.base_adapter import BaseNotificationAdapter


class TelegramMessagePayloadSchema(BaseModel):
    message_text: str
    button_text: str
    button_link: str


class NotificationToTelegramMessageAdapter(
    BaseNotificationAdapter[TelegramMessagePayloadSchema]
):
    def build_url(self, path: str, params: dict[str, Any]) -> str:
        query_string = urlencode(
            {
                **params,
                "read_notification_id": self.notification.id,
            }
        )
        return f"{settings.frontend_app_base_url}{path}?{query_string}"

    def adapt_individual_invitation_accepted_v1(
        self,
        payload: InvitationAcceptanceNotificationPayloadSchema,
    ) -> TelegramMessagePayloadSchema:
        return TelegramMessagePayloadSchema(
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
    ) -> TelegramMessagePayloadSchema:
        return TelegramMessagePayloadSchema(
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
    ) -> TelegramMessagePayloadSchema:
        return TelegramMessagePayloadSchema(
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
    ) -> TelegramMessagePayloadSchema:
        return TelegramMessagePayloadSchema(
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
    ) -> TelegramMessagePayloadSchema:
        return TelegramMessagePayloadSchema(
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
    ) -> TelegramMessagePayloadSchema:
        return TelegramMessagePayloadSchema(
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
