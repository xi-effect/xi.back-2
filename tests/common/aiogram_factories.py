from aiogram.types import ChatMemberUpdated, Document, Message, Update, User
from pydantic import BaseModel

from tests.common.polyfactory_ext import BaseModelFactory


class BaseAiogramFactory[T: BaseModel](BaseModelFactory[T]):
    __is_base_factory__ = True
    __use_defaults__ = True


class UpdateFactory(BaseAiogramFactory[Update]):
    __model__ = Update


class MessageFactory(BaseAiogramFactory[Message]):
    __model__ = Message


class UserFactory(BaseAiogramFactory[User]):
    __model__ = User


class ChatMemberUpdatedFactory(BaseAiogramFactory[ChatMemberUpdated]):
    __model__ = ChatMemberUpdated


class DocumentFactory(BaseAiogramFactory[Document]):
    __model__ = Document
