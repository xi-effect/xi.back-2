from app.notifications.models.telegram_connections_db import TelegramConnection
from app.notifications.models.user_contacts_db import UserContact
from app.notifications.routes.telegram_connections_mub import TelegramMessageSchema
from tests.common.polyfactory_ext import BaseModelFactory, BasePatchModelFactory


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
