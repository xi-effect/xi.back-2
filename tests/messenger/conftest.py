from collections.abc import AsyncIterator
from uuid import UUID

import pytest

from app.common.dependencies.authorization_dep import ProxyAuthData
from app.messenger.models.chats_db import Chat
from app.messenger.models.messages_db import Message
from app.messenger.rooms import chat_room
from tests.common.active_session import ActiveSession
from tests.common.tmexio_testing import (
    TMEXIOListenerFactory,
    TMEXIOTestClient,
    TMEXIOTestServer,
)
from tests.common.types import AnyJSON
from tests.conftest import ProxyAuthDataFactory
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
async def chat_room_listener(
    tmexio_listener_factory: TMEXIOListenerFactory,
    chat: Chat,
) -> TMEXIOTestClient:
    return await tmexio_listener_factory(chat_room(chat.id))


@pytest.fixture()
def outsider_auth_data() -> ProxyAuthData:
    return ProxyAuthDataFactory.build()


@pytest.fixture()
def outsider_user_id(outsider_auth_data: ProxyAuthData) -> int:
    return outsider_auth_data.user_id


@pytest.fixture()
async def tmexio_outsider_client(
    tmexio_server: TMEXIOTestServer,
    outsider_auth_data: ProxyAuthData,
) -> AsyncIterator[TMEXIOTestClient]:
    async with tmexio_server.authorized_client(outsider_auth_data) as client:
        yield client


@pytest.fixture()
def sender_auth_data() -> ProxyAuthData:
    return ProxyAuthDataFactory.build()


@pytest.fixture()
def sender_user_id(sender_auth_data: ProxyAuthData) -> int:
    return sender_auth_data.user_id


@pytest.fixture()
async def tmexio_sender_client(
    tmexio_server: TMEXIOTestServer,
    sender_auth_data: ProxyAuthData,
) -> AsyncIterator[TMEXIOTestClient]:
    async with tmexio_server.authorized_client(sender_auth_data) as client:
        yield client


@pytest.fixture()
async def message(
    active_session: ActiveSession, chat: Chat, sender_user_id: int
) -> Message:
    async with active_session():
        return await Message.create(
            chat_id=chat.id,
            sender_user_id=sender_user_id,
            **factories.MessageInputFactory.build_python(),
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


MESSAGE_LIST_SIZE = 6


@pytest.fixture()
async def messages_data(
    active_session: ActiveSession,
    chat: Chat,
) -> AsyncIterator[list[AnyJSON]]:
    async with active_session():
        messages = [
            await Message.create(
                chat_id=chat.id,
                **factories.MessageInputMUBFactory.build_json(),
            )
            for _ in range(MESSAGE_LIST_SIZE)
        ]
    messages.sort(key=lambda message: message.created_at, reverse=True)

    yield [
        Message.ResponseSchema.model_validate(message, from_attributes=True).model_dump(
            mode="json"
        )
        for message in messages
    ]

    async with active_session():
        for message in messages:
            await message.delete()
