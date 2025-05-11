from aiogram.types import ChatMemberUpdated, Document, Message, Update, User
from polyfactory.factories.pydantic_factory import ModelFactory

from tests.common.polyfactory_ext import BaseModelFactory


class UpdateFactory(BaseModelFactory[Update]):
    __model__ = Update


class MessageFactory(BaseModelFactory[Message]):
    __model__ = Message


class UserFactory(ModelFactory[User]):
    __model__ = User


class ChatMemberUpdatedFactory(BaseModelFactory[ChatMemberUpdated]):
    __model__ = ChatMemberUpdated


class DocumentFactory(ModelFactory[Document]):
    __model__ = Document
