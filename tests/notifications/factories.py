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


class NotificationSimpleInputSchema(BaseModel):
    payload: notifications_sch.AnyNotificationPayloadSchema


class NotificationSimpleInputFactory(BaseModelFactory[NotificationSimpleInputSchema]):
    __model__ = NotificationSimpleInputSchema


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
