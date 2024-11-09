from app.messenger.models.chats_db import Chat
from app.messenger.models.messages_db import Message
from tests.common.polyfactory_ext import BaseModelFactory


class ChatInputFactory(BaseModelFactory[Chat.InputSchema]):
    __model__ = Chat.InputSchema


class MessageInputFactory(BaseModelFactory[Message.InputSchema]):
    __model__ = Message.InputSchema


class MessageInputMUBFactory(BaseModelFactory[Message.InputMUBSchema]):
    __model__ = Message.InputMUBSchema
