import pytest

from app.messenger.models.chats_db import Chat
from tests.common.active_session import ActiveSession


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
