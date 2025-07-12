import pytest
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage
from starlette.testclient import TestClient

from app.common.aiogram_ext import TelegramApp
from app.supbot import texts
from app.supbot.config import telegram_app
from app.supbot.models.support_db import SupportTicket
from tests.common.active_session import ActiveSession
from tests.common.aiogram_testing import MockedBot, TelegramBotWebhookDriver
from tests.common.id_provider import IDProvider


@pytest.fixture(scope="session")
def supbot_webhook_url() -> str:
    return "/api/public/supbot-service/telegram-updates/"


@pytest.fixture(scope="session")
def supbot_group_id(id_provider: IDProvider) -> int:
    return id_provider.generate_id()


@pytest.fixture(scope="session")
def supbot_webhook_driver(
    client: TestClient,
    supbot_webhook_url: str,
) -> TelegramBotWebhookDriver:
    return TelegramBotWebhookDriver(
        client=client,
        webhook_url=supbot_webhook_url,
    )


@pytest.fixture(autouse=True, scope="session")
def mocked_telegram_app(
    bot: Bot,
    base_bot_storage: MemoryStorage,
    supbot_group_id: int,
) -> TelegramApp:
    telegram_app.initialize(
        bot=bot,
        dispatcher=Dispatcher(
            storage=base_bot_storage,
            group_id=supbot_group_id,
        ),
    )
    return telegram_app


@pytest.fixture()
def message_thread_id(id_provider: IDProvider) -> int:
    return id_provider.generate_id()


@pytest.fixture()
def message_id(id_provider: IDProvider) -> int:
    return id_provider.generate_id()


@pytest.fixture()
def bot_storage_key(
    mocked_bot: MockedBot,
    tg_user_id: int,
    tg_chat_id: int,
) -> StorageKey:
    return StorageKey(
        bot_id=mocked_bot.id,
        chat_id=tg_chat_id,
        user_id=tg_user_id,
    )


@pytest.fixture()
async def support_ticket(
    active_session: ActiveSession, message_thread_id: int, tg_chat_id: int
) -> SupportTicket:
    async with active_session():
        return await SupportTicket.create(
            message_thread_id=message_thread_id, chat_id=tg_chat_id
        )


EXPECTED_MAIN_MENU_KEYBOARD_MARKUP = {
    "keyboard": [[{"text": command.description} for command in texts.BOT_COMMANDS]],
    "resize_keyboard": True,
}
