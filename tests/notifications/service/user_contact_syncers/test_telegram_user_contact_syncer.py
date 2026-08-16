from unittest.mock import Mock

import pytest
from aiogram import Bot
from aiogram.types import ChatMemberMember
from faker import Faker

from app.notifications.services.user_contact_syncers.telegram_user_contact_syncer import (
    TelegramUserContactSyncer,
)
from tests.common.aiogram_factories import UserFactory
from tests.common.mock_stack import MockStack

pytestmark = pytest.mark.anyio


async def test_telegram_user_contact_link_building(
    faker: Faker,
    active_telegram_user_contact_syncer: TelegramUserContactSyncer,
) -> None:
    username: str = faker.user_name()

    assert (
        active_telegram_user_contact_syncer.username_to_link(username=username)
        == f"https://t.me/{username}"
    )


@pytest.mark.parametrize(
    "has_username",
    [
        pytest.param(True, id="with_username"),
        pytest.param(False, id="no_username"),
    ],
)
async def test_telegram_user_contact_syncing_from_message(
    faker: Faker,
    mock_stack: MockStack,
    active_telegram_user_contact_syncer: TelegramUserContactSyncer,
    has_username: bool,
) -> None:
    username: str | None = faker.user_name() if has_username else None
    message_mock = Mock()
    message_mock.from_user.username = username
    upsert_from_username_mock = mock_stack.enter_async_mock(
        active_telegram_user_contact_syncer,
        "upsert_from_username",
    )

    user_contact = await active_telegram_user_contact_syncer.sync_from_message(
        message=message_mock,
    )

    if username is None:
        assert user_contact is None
        upsert_from_username_mock.assert_not_called()
    else:
        assert user_contact is upsert_from_username_mock.return_value
        upsert_from_username_mock.assert_awaited_once_with(username=username)


@pytest.mark.parametrize(
    "has_username",
    [
        pytest.param(True, id="with_username"),
        pytest.param(False, id="no_username"),
    ],
)
async def test_telegram_username_retrieving(
    faker: Faker,
    mock_stack: MockStack,
    bot_id: int,
    bot: Bot,
    tg_chat_id: int,
    active_telegram_user_contact_syncer: TelegramUserContactSyncer,
    has_username: bool,
) -> None:
    username: str | None = faker.user_name() if has_username else None
    get_chat_member_mock = mock_stack.enter_async_mock(
        bot,
        "get_chat_member",
        return_value=ChatMemberMember(
            user=UserFactory.build(id=bot_id, username=username),
        ),
    )

    assert (
        await active_telegram_user_contact_syncer.retrieve_current_username()
    ) == username

    get_chat_member_mock.assert_awaited_once_with(
        chat_id=tg_chat_id,
        user_id=tg_chat_id,
    )
