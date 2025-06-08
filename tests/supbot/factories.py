from aiogram.types import ChatMemberUpdated, Document, Message, Update, User

from tests.common.polyfactory_ext import BaseModelFactory


class UpdateFactory(BaseModelFactory[Update]):
    __model__ = Update


class MessageFactory(BaseModelFactory[Message]):
    __model__ = Message


class UserFactory(BaseModelFactory[User]):
    __model__ = User


class ChatMemberUpdatedFactory(BaseModelFactory[ChatMemberUpdated]):
    __model__ = ChatMemberUpdated


class DocumentFactory(BaseModelFactory[Document]):
    __model__ = Document
