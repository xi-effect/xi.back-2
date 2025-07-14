import pytest
from aiogram import Bot
from aiogram.enums import ChatMemberStatus
from aiogram.fsm.storage.base import BaseStorage, StorageKey
from aiogram.methods import CloseForumTopic, CopyMessage, EditForumTopic, SendMessage
from aiogram.types import Chat, ChatMemberBanned, ChatMemberMember
from aiogram.types.forum_topic import ForumTopic
from faker import Faker

from app.common.utils.datetime import datetime_utc_now
from app.supbot import texts
from app.supbot.models.support_db import SupportTicket
from app.supbot.routers.support_tgm import Support
from tests.common.aiogram_factories import (
    ChatMemberUpdatedFactory,
    MessageFactory,
    UpdateFactory,
    UserFactory,
)
from tests.common.aiogram_testing import MockedBot, TelegramBotWebhookDriver
from tests.common.mock_stack import MockStack
from tests.supbot.conftest import EXPECTED_MAIN_MENU_KEYBOARD_MARKUP

pytestmark = pytest.mark.anyio


async def test_starting_support(
    supbot_webhook_driver: TelegramBotWebhookDriver,
    mocked_bot: MockedBot,
    bot_storage: BaseStorage,
    bot_storage_key: StorageKey,
    tg_chat_id: int,
    tg_user_id: int,
) -> None:
    supbot_webhook_driver.feed_update(
        UpdateFactory.build(
            message=MessageFactory.build(
                text="/support",
                chat=Chat(id=tg_chat_id, type="private"),
                from_user=UserFactory.build(id=tg_user_id),
            ),
        )
    )

    assert await bot_storage.get_state(bot_storage_key) == Support.start

    mocked_bot.assert_next_api_call(
        SendMessage,
        {
            "chat_id": tg_chat_id,
            "text": texts.START_SUPPORT_MESSAGE,
            "reply_markup": {
                "keyboard": [[{"text": texts.MAIN_MENU_BUTTON_TEXT}]],
            },
        },
    )
    mocked_bot.assert_no_more_api_calls()


async def test_exiting_support(
    supbot_webhook_driver: TelegramBotWebhookDriver,
    mocked_bot: MockedBot,
    bot_storage: BaseStorage,
    bot_storage_key: StorageKey,
    tg_chat_id: int,
    tg_user_id: int,
) -> None:
    await bot_storage.set_state(bot_storage_key, Support.start)

    supbot_webhook_driver.feed_update(
        UpdateFactory.build(
            message=MessageFactory.build(
                text=texts.MAIN_MENU_BUTTON_TEXT,
                chat=Chat(id=tg_chat_id, type="private"),
                from_user=UserFactory.build(id=tg_user_id),
            ),
        )
    )

    assert await bot_storage.get_state(bot_storage_key) is None

    mocked_bot.assert_next_api_call(
        SendMessage,
        {
            "chat_id": tg_chat_id,
            "text": texts.MAIN_MENU_MESSAGE,
            "reply_markup": EXPECTED_MAIN_MENU_KEYBOARD_MARKUP,
        },
    )
    mocked_bot.assert_no_more_api_calls()


async def test_creating_support_ticket(
    faker: Faker,
    mock_stack: MockStack,
    supbot_webhook_driver: TelegramBotWebhookDriver,
    bot: Bot,
    mocked_bot: MockedBot,
    bot_storage: BaseStorage,
    bot_storage_key: StorageKey,
    supbot_group_id: int,
    message_thread_id: int,
    tg_chat_id: int,
    tg_user_id: int,
) -> None:
    topic_mock = mock_stack.enter_async_mock(
        bot,
        "create_forum_topic",
        return_value=ForumTopic(
            message_thread_id=message_thread_id,
            name=faker.name(),
            icon_color=faker.pyint(),
        ),
    )

    await bot_storage.set_state(bot_storage_key, Support.start)

    username: str = faker.user_name()
    supbot_webhook_driver.feed_update(
        UpdateFactory.build(
            message=MessageFactory.build(
                chat=Chat(id=tg_chat_id, type="private", username=username),
                from_user=UserFactory.build(id=tg_user_id),
            ),
        ),
    )

    topic_mock.assert_called_once_with(
        chat_id=supbot_group_id,
        name=texts.SUPPORT_TOPIC_NAME_TEMPLATE.format(username=username),
        icon_custom_emoji_id=texts.SUPPORT_TICKED_OPENED_EMOJI_ID,
    )

    assert await bot_storage.get_state(bot_storage_key) == Support.conversation

    mocked_bot.assert_next_api_call(
        CopyMessage,
        {
            "chat_id": supbot_group_id,
            "from_chat_id": tg_chat_id,
            "message_thread_id": message_thread_id,
        },
    )
    mocked_bot.assert_next_api_call(
        SendMessage,
        {
            "chat_id": tg_chat_id,
            "text": texts.WAIT_SUPPORT_MESSAGE,
            "reply_markup": {
                "keyboard": [[{"text": texts.CLOSE_SUPPORT_BUTTON_TEXT}]],
            },
        },
    )
    mocked_bot.assert_no_more_api_calls()


async def test_sending_message_to_support(
    supbot_webhook_driver: TelegramBotWebhookDriver,
    mocked_bot: MockedBot,
    bot_storage: BaseStorage,
    bot_storage_key: StorageKey,
    supbot_group_id: int,
    tg_chat_id: int,
    tg_user_id: int,
    support_ticket: SupportTicket,
) -> None:
    await bot_storage.update_data(
        bot_storage_key, {"thread_id": support_ticket.message_thread_id}
    )
    await bot_storage.set_state(bot_storage_key, Support.conversation)

    supbot_webhook_driver.feed_update(
        UpdateFactory.build(
            message=MessageFactory.build(
                chat=Chat(id=tg_chat_id, type="private"),
                from_user=UserFactory.build(id=tg_user_id),
            ),
        ),
    )

    mocked_bot.assert_next_api_call(
        CopyMessage,
        {
            "chat_id": supbot_group_id,
            "from_chat_id": tg_chat_id,
            "message_thread_id": support_ticket.message_thread_id,
        },
    )
    mocked_bot.assert_no_more_api_calls()


async def test_closing_support_ticket_by_user(
    supbot_webhook_driver: TelegramBotWebhookDriver,
    mocked_bot: MockedBot,
    bot_storage: BaseStorage,
    bot_storage_key: StorageKey,
    supbot_group_id: int,
    tg_chat_id: int,
    tg_user_id: int,
    support_ticket: SupportTicket,
) -> None:
    await bot_storage.update_data(
        bot_storage_key, {"thread_id": support_ticket.message_thread_id}
    )
    await bot_storage.set_state(bot_storage_key, Support.conversation)

    supbot_webhook_driver.feed_update(
        UpdateFactory.build(
            message=MessageFactory.build(
                text=texts.CLOSE_SUPPORT_BUTTON_TEXT,
                chat=Chat(id=tg_chat_id, type="private"),
                from_user=UserFactory.build(id=tg_user_id),
            ),
        ),
    )

    assert await bot_storage.get_state(bot_storage_key) is None

    mocked_bot.assert_next_api_call(
        CloseForumTopic,
        {
            "chat_id": supbot_group_id,
            "message_thread_id": support_ticket.message_thread_id,
        },
    )
    mocked_bot.assert_next_api_call(
        EditForumTopic,
        {
            "chat_id": supbot_group_id,
            "message_thread_id": support_ticket.message_thread_id,
            "icon_custom_emoji_id": texts.SUPPORT_TICKET_CLOSED_EMOJI_ID,
        },
    )
    mocked_bot.assert_next_api_call(
        SendMessage,
        {
            "chat_id": supbot_group_id,
            "text": texts.TICKET_CLOSED_BY_USER_MESSAGE,
            "message_thread_id": support_ticket.message_thread_id,
        },
    )
    mocked_bot.assert_next_api_call(
        SendMessage,
        {
            "chat_id": tg_chat_id,
            "text": texts.CLOSE_TICKET_CONFIRMATION_MESSAGE,
            "reply_markup": EXPECTED_MAIN_MENU_KEYBOARD_MARKUP,
        },
    )
    mocked_bot.assert_no_more_api_calls()


async def test_closing_ticket_after_user_banned_bot(
    supbot_webhook_driver: TelegramBotWebhookDriver,
    mocked_bot: MockedBot,
    bot_storage: BaseStorage,
    bot_storage_key: StorageKey,
    supbot_group_id: int,
    tg_chat_id: int,
    tg_user_id: int,
    support_ticket: SupportTicket,
) -> None:
    await bot_storage.update_data(
        bot_storage_key, {"thread_id": support_ticket.message_thread_id}
    )
    await bot_storage.set_state(bot_storage_key, Support.conversation)

    supbot_webhook_driver.feed_update(
        UpdateFactory.build(
            my_chat_member=ChatMemberUpdatedFactory.build(
                chat=Chat(id=tg_chat_id, type="private"),
                from_user=UserFactory.build(id=tg_user_id),
                old_chat_member=ChatMemberMember(
                    user=UserFactory.build(id=tg_user_id),
                    status=ChatMemberStatus.MEMBER,
                ),
                new_chat_member=ChatMemberBanned(
                    user=UserFactory.build(id=tg_user_id),
                    status=ChatMemberStatus.KICKED,
                    until_date=datetime_utc_now(),
                ),
            ),
        )
    )

    assert await bot_storage.get_state(bot_storage_key) is None

    mocked_bot.assert_next_api_call(
        CloseForumTopic,
        {
            "chat_id": supbot_group_id,
            "message_thread_id": support_ticket.message_thread_id,
        },
    )
    mocked_bot.assert_next_api_call(
        EditForumTopic,
        {
            "chat_id": supbot_group_id,
            "message_thread_id": support_ticket.message_thread_id,
            "icon_custom_emoji_id": texts.SUPPORT_TICKET_CLOSED_EMOJI_ID,
        },
    )
    mocked_bot.assert_next_api_call(
        SendMessage,
        {
            "chat_id": supbot_group_id,
            "text": texts.TICKET_CLOSED_AFTER_USER_BANNED_BOT_MESSAGE,
            "message_thread_id": support_ticket.message_thread_id,
        },
    )
    mocked_bot.assert_no_more_api_calls()
