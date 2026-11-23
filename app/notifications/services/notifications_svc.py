from typing import Any, assert_never

from app.common.schemas.notifications_sch import (
    ClassroomNotificationPayloadSchema,
    ClassroomScheduleFocusNotificationPayloadSchema,
    CustomNotificationPayloadSchema,
    EnrollmentNotificationPayloadSchema,
    InvitationAcceptanceNotificationPayloadSchema,
    NotificationKind,
    PersistedClassroomEventInstanceNotificationPayloadSchema,
    RecipientInvoiceNotificationPayloadSchema,
    RepeatedClassroomEventInstanceNotificationPayloadSchema,
)
from app.notifications.models.notifications_db import Notification
from app.notifications.services.notification_adapters import (
    base_notification_adapter,
    classroom_notification_adapters,
    custom_notification_adapters,
    event_notification_adapters,
    recipient_invoice_notification_adapters,
)


def build_notification_adapter(
    notification: Notification,
) -> base_notification_adapter.BaseNotificationAdapter[Any]:
    payload = notification.payload
    match payload:
        case InvitationAcceptanceNotificationPayloadSchema():
            match payload.kind:
                case NotificationKind.INDIVIDUAL_INVITATION_ACCEPTED_V1:
                    return classroom_notification_adapters.IndividualInvitationAcceptedV1NotificationAdapter(
                        notification=notification,
                        payload=payload,
                    )
                case NotificationKind.GROUP_INVITATION_ACCEPTED_V1:
                    return classroom_notification_adapters.GroupInvitationAcceptedV1NotificationAdapter(
                        notification=notification,
                        payload=payload,
                    )
                case _:
                    assert_never(payload.kind)
        case EnrollmentNotificationPayloadSchema():
            match payload.kind:
                case NotificationKind.ENROLLMENT_CREATED_V1:
                    return classroom_notification_adapters.EnrollmentCreatedV1NotificationAdapter(
                        notification=notification,
                        payload=payload,
                    )
                case _:
                    assert_never(payload.kind)
        case ClassroomNotificationPayloadSchema():
            match payload.kind:
                case NotificationKind.CLASSROOM_CONFERENCE_STARTED_V1:
                    return classroom_notification_adapters.ClassroomConferenceStartedV1NotificationAdapter(
                        notification=notification,
                        payload=payload,
                    )
                case _:
                    assert_never(payload.kind)
        case RecipientInvoiceNotificationPayloadSchema():
            match payload.kind:
                case NotificationKind.RECIPIENT_INVOICE_CREATED_V1:
                    return recipient_invoice_notification_adapters.RecipientInvoiceCreatedV1NotificationAdapter(
                        notification=notification,
                        payload=payload,
                    )
                case NotificationKind.STUDENT_RECIPIENT_INVOICE_PAYMENT_CONFIRMED_V1:
                    return recipient_invoice_notification_adapters.StudentRecipientInvoicePaymentConfirmedV1NotificationAdapter(
                        notification=notification,
                        payload=payload,
                    )
                case _:
                    assert_never(payload.kind)
        case PersistedClassroomEventInstanceNotificationPayloadSchema():
            match payload.kind:
                case NotificationKind.SINGLE_CLASSROOM_EVENT_CREATED_V1:
                    return event_notification_adapters.SingleClassroomEventCreatedV1NotificationAdapter(
                        notification=notification,
                        payload=payload,
                    )
                case NotificationKind.CLASSROOM_EVENT_INSTANCE_RESCHEDULED_V1:
                    return event_notification_adapters.ClassroomEventInstanceRescheduledV1NotificationAdapter(
                        notification=notification,
                        payload=payload,
                    )
                case NotificationKind.CLASSROOM_EVENT_INSTANCE_CANCELLED_V1:
                    return event_notification_adapters.ClassroomEventInstanceCancelledV1NotificationAdapter(
                        notification=notification,
                        payload=payload,
                    )
                case NotificationKind.PERSISTED_CLASSROOM_EVENT_INSTANCE_REMINDER_V1:
                    return event_notification_adapters.PersistedClassroomEventInstanceReminderV1NotificationAdapter(
                        notification=notification,
                        payload=payload,
                    )
                case _:
                    assert_never(payload.kind)
        case RepeatedClassroomEventInstanceNotificationPayloadSchema():
            match payload.kind:
                case NotificationKind.REPEATED_CLASSROOM_EVENT_INSTANCE_REMINDER_V1:
                    return event_notification_adapters.RepeatedClassroomEventInstanceReminderV1NotificationAdapter(
                        notification=notification,
                        payload=payload,
                    )
                case _:
                    assert_never(payload.kind)
        case ClassroomScheduleFocusNotificationPayloadSchema():
            match payload.kind:
                case NotificationKind.REPEATING_CLASSROOM_EVENT_CREATED_V1:
                    return event_notification_adapters.RepeatingClassroomEventCreatedV1NotificationAdapter(
                        notification=notification,
                        payload=payload,
                    )
                case NotificationKind.CLASSROOM_EVENT_REPETITION_UPDATED_V1:
                    return event_notification_adapters.ClassroomEventRepetitionUpdatedV1NotificationAdapter(
                        notification=notification,
                        payload=payload,
                    )
                case NotificationKind.CLASSROOM_EVENT_REPETITION_CANCELLED_V1:
                    return event_notification_adapters.ClassroomEventRepetitionCancelledV1NotificationAdapter(
                        notification=notification,
                        payload=payload,
                    )
                case _:
                    assert_never(payload.kind)
        case CustomNotificationPayloadSchema():
            match payload.kind:
                case NotificationKind.CUSTOM_V1:
                    return custom_notification_adapters.CustomV1NotificationAdapter(
                        notification=notification,
                        payload=payload,
                    )
                case _:
                    assert_never(payload.kind)
        case _:
            assert_never(payload)
