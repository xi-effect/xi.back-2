from pydantic import BaseModel

from app.common.schemas import notifications_sch
from app.notifications.models.email_connections_db import EmailConnection
from app.notifications.models.telegram_connections_db import TelegramConnection
from app.notifications.models.user_contacts_db import UserContact
from app.notifications.routes.telegram_connections_mub import TelegramMessageSchema
from tests.common.polyfactory_ext import BaseModelFactory, BasePatchModelFactory


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


class ClassroomEventInstanceNotificationPayloadFactory(
    BaseModelFactory[notifications_sch.ClassroomEventInstanceNotificationPayloadSchema]
):
    __model__ = notifications_sch.ClassroomEventInstanceNotificationPayloadSchema


class ClassroomScheduleFocusNotificationPayloadFactory(
    BaseModelFactory[notifications_sch.ClassroomScheduleFocusNotificationPayloadSchema]
):
    __model__ = notifications_sch.ClassroomScheduleFocusNotificationPayloadSchema


class CustomNotificationPayloadFactory(
    BaseModelFactory[notifications_sch.CustomNotificationPayloadSchema]
):
    __model__ = notifications_sch.CustomNotificationPayloadSchema


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


class EmailConnectionInputFactory(BaseModelFactory[EmailConnection.InputSchema]):
    __model__ = EmailConnection.InputSchema


class TelegramConnectionInputMUBFactory(
    BaseModelFactory[TelegramConnection.InputMUBSchema]
):
    __model__ = TelegramConnection.InputMUBSchema


class TelegramConnectionPatchMUBFactory(
    BasePatchModelFactory[TelegramConnection.PatchMUBSchema]
):
    __model__ = TelegramConnection.PatchMUBSchema


class TelegramMessageFactory(BaseModelFactory[TelegramMessageSchema]):
    __model__ = TelegramMessageSchema


class UserContactInputFactory(BaseModelFactory[UserContact.InputSchema]):
    __model__ = UserContact.InputSchema
