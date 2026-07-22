from datetime import UTC
from typing import Any

from polyfactory import Use
from pydantic import BaseModel

from app.common.schemas import notifications_sch
from app.notifications.models.delivery_methods_db import EmailDeliveryMethod
from app.notifications.models.user_contacts_db import UserContact
from app.notifications.schemas.vk import (
    vk_base_sch,
    vk_messages_sch,
    vk_updates_sch,
)
from tests.common.polyfactory_ext import BaseModelFactory


class InvitationAcceptanceNotificationPayloadFactory(
    BaseModelFactory[notifications_sch.InvitationAcceptanceNotificationPayloadSchema]
):
    __model__ = notifications_sch.InvitationAcceptanceNotificationPayloadSchema


class EnrollmentNotificationPayloadFactory(
    BaseModelFactory[notifications_sch.EnrollmentNotificationPayloadSchema]
):
    __model__ = notifications_sch.EnrollmentNotificationPayloadSchema


class ClassroomNotificationPayloadFactory(
    BaseModelFactory[notifications_sch.ClassroomNotificationPayloadSchema]
):
    __model__ = notifications_sch.ClassroomNotificationPayloadSchema


class RecipientInvoiceNotificationPayloadFactory(
    BaseModelFactory[notifications_sch.RecipientInvoiceNotificationPayloadSchema]
):
    __model__ = notifications_sch.RecipientInvoiceNotificationPayloadSchema


class PersistedClassroomEventInstanceNotificationPayloadFactory(
    BaseModelFactory[
        notifications_sch.PersistedClassroomEventInstanceNotificationPayloadSchema
    ]
):
    __model__ = (
        notifications_sch.PersistedClassroomEventInstanceNotificationPayloadSchema
    )


class RepeatedClassroomEventInstanceNotificationPayloadFactory(
    BaseModelFactory[
        notifications_sch.RepeatedClassroomEventInstanceNotificationPayloadSchema
    ]
):
    __model__ = (
        notifications_sch.RepeatedClassroomEventInstanceNotificationPayloadSchema
    )


class ClassroomScheduleFocusNotificationPayloadFactory(
    BaseModelFactory[notifications_sch.ClassroomScheduleFocusNotificationPayloadSchema]
):
    __model__ = notifications_sch.ClassroomScheduleFocusNotificationPayloadSchema


class CustomNotificationPayloadFactory(
    BaseModelFactory[notifications_sch.CustomNotificationPayloadSchema]
):
    __model__ = notifications_sch.CustomNotificationPayloadSchema


NOTIFICATION_KIND_TO_PAYLOAD_FACTORY: dict[
    notifications_sch.NotificationKind, type[BaseModelFactory[Any]]
] = {
    notifications_sch.NotificationKind.INDIVIDUAL_INVITATION_ACCEPTED_V1: InvitationAcceptanceNotificationPayloadFactory,
    notifications_sch.NotificationKind.GROUP_INVITATION_ACCEPTED_V1: InvitationAcceptanceNotificationPayloadFactory,
    notifications_sch.NotificationKind.ENROLLMENT_CREATED_V1: EnrollmentNotificationPayloadFactory,
    notifications_sch.NotificationKind.CLASSROOM_CONFERENCE_STARTED_V1: ClassroomNotificationPayloadFactory,
    notifications_sch.NotificationKind.RECIPIENT_INVOICE_CREATED_V1: RecipientInvoiceNotificationPayloadFactory,
    notifications_sch.NotificationKind.STUDENT_RECIPIENT_INVOICE_PAYMENT_CONFIRMED_V1: RecipientInvoiceNotificationPayloadFactory,
    notifications_sch.NotificationKind.SINGLE_CLASSROOM_EVENT_CREATED_V1: PersistedClassroomEventInstanceNotificationPayloadFactory,
    notifications_sch.NotificationKind.CLASSROOM_EVENT_INSTANCE_RESCHEDULED_V1: PersistedClassroomEventInstanceNotificationPayloadFactory,
    notifications_sch.NotificationKind.CLASSROOM_EVENT_INSTANCE_CANCELLED_V1: PersistedClassroomEventInstanceNotificationPayloadFactory,
    notifications_sch.NotificationKind.PERSISTED_CLASSROOM_EVENT_INSTANCE_REMINDER_V1: PersistedClassroomEventInstanceNotificationPayloadFactory,
    notifications_sch.NotificationKind.REPEATED_CLASSROOM_EVENT_INSTANCE_REMINDER_V1: RepeatedClassroomEventInstanceNotificationPayloadFactory,
    notifications_sch.NotificationKind.REPEATING_CLASSROOM_EVENT_CREATED_V1: ClassroomScheduleFocusNotificationPayloadFactory,
    notifications_sch.NotificationKind.CLASSROOM_EVENT_REPETITION_UPDATED_V1: ClassroomScheduleFocusNotificationPayloadFactory,
    notifications_sch.NotificationKind.CLASSROOM_EVENT_REPETITION_CANCELLED_V1: ClassroomScheduleFocusNotificationPayloadFactory,
    notifications_sch.NotificationKind.CUSTOM_V1: CustomNotificationPayloadFactory,
}


class NotificationSimpleInputSchema(BaseModel):
    payload: notifications_sch.AnyNotificationPayloadSchema


class NotificationSimpleInputFactory(BaseModelFactory[NotificationSimpleInputSchema]):
    __model__ = NotificationSimpleInputSchema


class SingleUserRecipientFilterFactory(
    BaseModelFactory[notifications_sch.SingleUserRecipientFilterSchema]
):
    __model__ = notifications_sch.SingleUserRecipientFilterSchema


class ClassroomParticipantRecipientFilterFactory(
    BaseModelFactory[notifications_sch.ClassroomParticipantRecipientFilterSchema]
):
    __model__ = notifications_sch.ClassroomParticipantRecipientFilterSchema


class NotificationInputV2Factory(
    BaseModelFactory[notifications_sch.NotificationInputV2Schema]
):
    __model__ = notifications_sch.NotificationInputV2Schema


class NotificationInputV2WithIdempotencyFactory(
    BaseModelFactory[notifications_sch.NotificationInputV2Schema]
):
    __model__ = notifications_sch.NotificationInputV2Schema

    idempotency_key = Use(BaseModelFactory.__faker__.pystr, min_chars=3)
    idempotency_expires_at = Use(BaseModelFactory.__faker__.future_datetime, tzinfo=UTC)


class EmailDeliveryMethodInputFactory(
    BaseModelFactory[EmailDeliveryMethod.InputSchema]
):
    __model__ = EmailDeliveryMethod.InputSchema


class UserContactInputFactory(BaseModelFactory[UserContact.InputSchema]):
    __model__ = UserContact.InputSchema


class ConfirmationUpdateFactory(
    BaseModelFactory[vk_updates_sch.ConfirmationUpdateSchema]
):
    __model__ = vk_updates_sch.ConfirmationUpdateSchema


class AllowMessagesObjectFactory(
    BaseModelFactory[vk_updates_sch.AllowMessagesObjectSchema]
):
    __model__ = vk_updates_sch.AllowMessagesObjectSchema


class AllowMessagesUpdateFactory(
    BaseModelFactory[vk_updates_sch.AllowMessagesUpdateSchema]
):
    __model__ = vk_updates_sch.AllowMessagesUpdateSchema


class DenyMessagesObjectFactory(
    BaseModelFactory[vk_updates_sch.DenyMessagesObjectSchema]
):
    __model__ = vk_updates_sch.DenyMessagesObjectSchema


class DenyMessagesUpdateFactory(
    BaseModelFactory[vk_updates_sch.DenyMessagesUpdateSchema]
):
    __model__ = vk_updates_sch.DenyMessagesUpdateSchema


class MessageSendResponseItemFactory(
    BaseModelFactory[vk_messages_sch.MessageSendResponseItemSchema]
):
    __model__ = vk_messages_sch.MessageSendResponseItemSchema


class MessageSendPeerErrorFactory(
    BaseModelFactory[vk_messages_sch.MessageSendPeerErrorSchema]
):
    __model__ = vk_messages_sch.MessageSendPeerErrorSchema


class ErrorFactory(BaseModelFactory[vk_base_sch.ErrorSchema]):
    __model__ = vk_base_sch.ErrorSchema
