from app.messenger.models.chat_users_db import ChatUser
from app.messenger.models.chats_db import Chat
from app.messenger.models.message_drafts_db import MessageDraft
from app.messenger.models.messages_db import Message
from tests.common.polyfactory_ext import BaseModelFactory, BasePatchModelFactory


class ChatInputFactory(BaseModelFactory[Chat.InputSchema]):
    __model__ = Chat.InputSchema


class ChatUserInputFactory(BaseModelFactory[ChatUser.InputSchema]):
    __model__ = ChatUser.InputSchema


class ChatUserPatchFactory(BasePatchModelFactory[ChatUser.PatchSchema]):
    __model__ = ChatUser.PatchSchema


class MessageInputFactory(BaseModelFactory[Message.InputSchema]):
    __model__ = Message.InputSchema


class MessageInputMUBFactory(BaseModelFactory[Message.InputMUBSchema]):
    __model__ = Message.InputMUBSchema


class MessagePatchMUBFactory(BasePatchModelFactory[Message.PatchMUBSchema]):
    __model__ = Message.PatchMUBSchema


class MessageDraftInputMUBFactory(BaseModelFactory[MessageDraft.InputSchema]):
    __model__ = MessageDraft.InputSchema


class MessageDraftPatchMUBFactory(BasePatchModelFactory[MessageDraft.PatchSchema]):
    __model__ = MessageDraft.PatchSchema
