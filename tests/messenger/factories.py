from app.messenger.models.chats_db import Chat
from tests.common.polyfactory_ext import BaseModelFactory


class ChatInputFactory(BaseModelFactory[Chat.InputSchema]):
    __model__ = Chat.InputSchema
