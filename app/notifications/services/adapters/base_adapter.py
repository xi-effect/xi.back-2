from abc import ABC, abstractmethod
from typing import Any, assert_never, cast
from urllib.parse import urlencode

from app.common.config import settings
from app.common.schemas.notifications_sch import (
    ClassroomEventInstanceNotificationPayloadSchema,
    ClassroomNotificationPayloadSchema,
    ClassroomScheduleFocusNotificationPayloadSchema,
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

    def build_url(self, path: str, params: dict[str, Any]) -> str:
        query_string = urlencode(
            {
                **params,
                "read_notification_id": self.notification.id,
            }
        )
        return f"{settings.frontend_app_base_url}{path}?{query_string}"

    def build_student_classroom_event_instance_url(
        self, payload: ClassroomEventInstanceNotificationPayloadSchema
    ) -> str:
        return self.build_url(
            path=f"/classrooms/{payload.classroom_id}",
            params={
                "tab": "schedule",
                "role": "student",
                "event_instance_id": payload.event_instance_id,
            },
        )

    def build_student_classroom_schedule_focus_url(
        self, payload: ClassroomScheduleFocusNotificationPayloadSchema
    ) -> str:
        return self.build_url(
            path=f"/classrooms/{payload.classroom_id}",
            params={
                "tab": "schedule",
                "role": "student",
                "focused_at": payload.focused_at.isoformat(),
            },
        )

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
    def adapt_single_classroom_event_created_v1(
        self,
        payload: ClassroomEventInstanceNotificationPayloadSchema,
    ) -> T:
        raise NotImplementedError

    @abstractmethod
    def adapt_classroom_event_instance_rescheduled_v1(
        self,
        payload: ClassroomEventInstanceNotificationPayloadSchema,
    ) -> T:
        raise NotImplementedError

    @abstractmethod
    def adapt_classroom_event_instance_cancelled_v1(
        self,
        payload: ClassroomEventInstanceNotificationPayloadSchema,
    ) -> T:
        raise NotImplementedError

    @abstractmethod
    def adapt_repeating_classroom_event_created_v1(
        self,
        payload: ClassroomScheduleFocusNotificationPayloadSchema,
    ) -> T:
        raise NotImplementedError

    @abstractmethod
    def adapt_classroom_event_repetition_updated_v1(
        self,
        payload: ClassroomScheduleFocusNotificationPayloadSchema,
    ) -> T:
        raise NotImplementedError

    @abstractmethod
    def adapt_classroom_event_repetition_cancelled_v1(
        self,
        payload: ClassroomScheduleFocusNotificationPayloadSchema,
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
            case NotificationKind.SINGLE_CLASSROOM_EVENT_CREATED_V1:
                return self.adapt_single_classroom_event_created_v1(
                    cast(ClassroomEventInstanceNotificationPayloadSchema, payload)
                )
            case NotificationKind.CLASSROOM_EVENT_INSTANCE_RESCHEDULED_V1:
                return self.adapt_classroom_event_instance_rescheduled_v1(
                    cast(ClassroomEventInstanceNotificationPayloadSchema, payload)
                )
            case NotificationKind.CLASSROOM_EVENT_INSTANCE_CANCELLED_V1:
                return self.adapt_classroom_event_instance_cancelled_v1(
                    cast(ClassroomEventInstanceNotificationPayloadSchema, payload)
                )
            case NotificationKind.REPEATING_CLASSROOM_EVENT_CREATED_V1:
                return self.adapt_repeating_classroom_event_created_v1(
                    cast(ClassroomScheduleFocusNotificationPayloadSchema, payload)
                )
            case NotificationKind.CLASSROOM_EVENT_REPETITION_UPDATED_V1:
                return self.adapt_classroom_event_repetition_updated_v1(
                    cast(ClassroomScheduleFocusNotificationPayloadSchema, payload)
                )
            case NotificationKind.CLASSROOM_EVENT_REPETITION_CANCELLED_V1:
                return self.adapt_classroom_event_repetition_cancelled_v1(
                    cast(ClassroomScheduleFocusNotificationPayloadSchema, payload)
                )
            case NotificationKind.CUSTOM_V1:
                return self.adapt_custom_v1(
                    cast(CustomNotificationPayloadSchema, payload)
                )
            case _:
                assert_never(payload.kind)
