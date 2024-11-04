from uuid import UUID

import pytest

from app.messenger.models.chats_db import Chat
from app.messenger.models.messages_db import Message
from tests.common.active_session import ActiveSession
from tests.common.types import AnyJSON
from tests.messenger import factories


@pytest.fixture()
def chat_data() -> AnyJSON:
    return factories.ChatInputFactory.build_json()


@pytest.fixture()
async def chat(active_session: ActiveSession, chat_data: AnyJSON) -> Chat:
    async with active_session():
        return await Chat.create(**chat_data)


@pytest.fixture()
async def deleted_chat_id(active_session: ActiveSession, chat: Chat) -> int:
    async with active_session():
        await chat.delete()
    return chat.id


@pytest.fixture()
async def message(
    active_session: ActiveSession,
    chat: Chat,
) -> Message:
    async with active_session():
        return await Message.create(
            chat_id=chat.id,
            **factories.MessageInputMUBFactory.build_json(),
        )


@pytest.fixture()
def message_data(message: Message) -> AnyJSON:
    return Message.ResponseSchema.model_validate(
        message, from_attributes=True
    ).model_dump(mode="json")


@pytest.fixture()
async def deleted_message_id(
    active_session: ActiveSession,
    message: Message,
) -> UUID:
    async with active_session():
        await message.delete()
    return message.id
