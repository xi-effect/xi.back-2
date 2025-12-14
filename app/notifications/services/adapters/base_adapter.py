from abc import ABC, abstractmethod
from typing import assert_never, cast

from app.common.schemas.notifications_sch import (
    ClassroomNotificationPayloadSchema,
    CustomNotificationPayloadSchema,
    EnrollmentNotificationPayloadSchema,
    InvitationAcceptanceNotificationPayloadSchema,
    NotificationKind,
    RecipientInvoiceNotificationPayloadSchema,
)
from app.notifications.models.notifications_db import Notification


class BaseNotificationAdapter[T](ABC):
    def __init__(self, notification: Notification) -> None:
        self.notification = notification

    @abstractmethod
    def adapt_individual_invitation_accepted_v1(
        self,
        payload: InvitationAcceptanceNotificationPayloadSchema,
    ) -> T:
        raise NotImplementedError

    @abstractmethod
    def adapt_group_invitation_accepted_v1(
        self,
        payload: InvitationAcceptanceNotificationPayloadSchema,
    ) -> T:
        raise NotImplementedError

    @abstractmethod
    def adapt_enrollment_created_v1(
        self,
        payload: EnrollmentNotificationPayloadSchema,
    ) -> T:
        raise NotImplementedError

    @abstractmethod
    def adapt_classroom_conference_started_v1(
        self,
        payload: ClassroomNotificationPayloadSchema,
    ) -> T:
        raise NotImplementedError

    @abstractmethod
    def adapt_recipient_invoice_created_v1(
        self,
        payload: RecipientInvoiceNotificationPayloadSchema,
    ) -> T:
        raise NotImplementedError

    @abstractmethod
    def adapt_student_recipient_invoice_payment_confirmed_v1(
        self,
        payload: RecipientInvoiceNotificationPayloadSchema,
    ) -> T:
        raise NotImplementedError

    @abstractmethod
    def adapt_custom_v1(
        self,
        payload: CustomNotificationPayloadSchema,
    ) -> T:
        raise NotImplementedError

    def adapt(self) -> T:
        # cast is used because mypy doesn't understand pydantic's discriminated unions
        payload = self.notification.payload
        match payload.kind:
            case NotificationKind.INDIVIDUAL_INVITATION_ACCEPTED_V1:
                return self.adapt_individual_invitation_accepted_v1(
                    cast(InvitationAcceptanceNotificationPayloadSchema, payload)
                )
            case NotificationKind.GROUP_INVITATION_ACCEPTED_V1:
                return self.adapt_group_invitation_accepted_v1(
                    cast(InvitationAcceptanceNotificationPayloadSchema, payload)
                )
            case NotificationKind.ENROLLMENT_CREATED_V1:
                return self.adapt_enrollment_created_v1(
                    cast(EnrollmentNotificationPayloadSchema, payload)
                )
            case NotificationKind.CLASSROOM_CONFERENCE_STARTED_V1:
                return self.adapt_classroom_conference_started_v1(
                    cast(ClassroomNotificationPayloadSchema, payload)
                )
            case NotificationKind.RECIPIENT_INVOICE_CREATED_V1:
                return self.adapt_recipient_invoice_created_v1(
                    cast(RecipientInvoiceNotificationPayloadSchema, payload)
                )
            case NotificationKind.STUDENT_RECIPIENT_INVOICE_PAYMENT_CONFIRMED_V1:
                return self.adapt_student_recipient_invoice_payment_confirmed_v1(
                    cast(RecipientInvoiceNotificationPayloadSchema, payload)
                )
            case NotificationKind.CUSTOM_V1:
                return self.adapt_custom_v1(
                    cast(CustomNotificationPayloadSchema, payload)
                )
            case _:
                assert_never(payload.kind)
