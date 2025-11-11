import logging
import warnings
from asyncio import create_task
from typing import Any

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import CommandObject
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.methods import GetUpdates
from aiogram.types import BotCommand, ChatMemberUpdated, Message, User
from httpx import AsyncClient

from app.common.config import TelegramBotSettings, settings
from app.common.dependencies.telegram_auth_dep import TELEGRAM_WEBHOOK_TOKEN_HEADER_NAME


class TelegramApp:
    def __init__(self) -> None:
        self.routers: list[Router] = []
        self._bot: Bot | None = None
        self._bot_username: str | None = None
        self._dispatcher: Dispatcher | None = None
        self._initialized: bool = False

    def include_router(self, router: Router) -> None:
        self.routers.append(router)

    async def initialize(self, bot: Bot, dispatcher: Dispatcher) -> None:
        if self._initialized:
            return
        self._bot = bot
        self._bot_username = (await bot.me()).username
        self._dispatcher = dispatcher
        for router in self.routers:
            self._dispatcher.include_router(router)
        self._initialized = True

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    @property
    def bot(self) -> Bot:
        if self._bot is None:
            raise EnvironmentError("Bot is not initialized")
        return self._bot

    @property
    def bot_username(self) -> str:
        if self._bot_username is None:
            raise EnvironmentError("Bot username is not initialized")
        return self._bot_username

    @property
    def dispatcher(self) -> Dispatcher:
        if self._dispatcher is None:
            raise EnvironmentError("Dispatcher is not initialized")
        return self._dispatcher

    async def feed_updates_into_webhook(
        self,
        webhook_url: str,
        webhook_token: str | None = None,
        polling_timeout: int = 30,
    ) -> None:
        async with AsyncClient(
            base_url=webhook_url,
            headers=(
                None
                if webhook_token is None
                else {TELEGRAM_WEBHOOK_TOKEN_HEADER_NAME: webhook_token}
            ),
        ) as client:
            # Partially copied from a protected function:
            # https://github.com/aiogram/aiogram/blob/756cfeba0a257d80b9450adda5c6f4eda743c031/aiogram/dispatcher/dispatcher.py#L191-L247
            get_updates = GetUpdates(timeout=polling_timeout)
            while True:  # noqa: WPS457  # we know
                updates = await self.bot(get_updates)
                for update in updates:
                    await client.post(
                        url="", json=update.model_dump(mode="json", exclude_unset=True)
                    )
                    get_updates.offset = update.update_id + 1

    async def maybe_initialize_from_config(
        self,
        *,
        bot_name: str,
        bot_settings: TelegramBotSettings | None,
        bot_commands: list[BotCommand] | None = None,
        allowed_updates: list[str] | None = None,
        max_connections: int = 40,
        webhook_prefix: str,
        webhook_path: str = "/telegram-updates/",
        redis_dsn: str | None = None,
        **dispatcher_kwargs: Any,
    ) -> None:
        if settings.is_testing_mode or bot_settings is None:
            if settings.production_mode:
                logging.warning(f"Configuration for {bot_name} is missing")
            return

        await self.initialize(
            bot=Bot(bot_settings.token),
            dispatcher=Dispatcher(
                storage=None if redis_dsn is None else RedisStorage.from_url(redis_dsn),
                **dispatcher_kwargs,
            ),
        )

        if bot_commands is not None:
            await self.bot.set_my_commands(bot_commands)

        full_webhook_path: str = f"{webhook_prefix}{webhook_path}"

        if settings.telegram_webhook_base_url is None:
            if settings.production_mode:
                logging.error("Polling shouldn't be used in production")
                return
            # noinspection PyAsyncCall
            # PyCharm can't comprehend background tasks
            create_task(
                self.feed_updates_into_webhook(
                    webhook_url=f"{settings.bridge_base_url}{full_webhook_path}",
                    webhook_token=bot_settings.webhook_token,
                )
            )
        else:
            await self.bot.set_webhook(
                url=f"{settings.telegram_webhook_base_url}{full_webhook_path}",
                secret_token=bot_settings.webhook_token,
                max_connections=max_connections,
                allowed_updates=allowed_updates,
            )


with warnings.catch_warnings():
    warnings.simplefilter("ignore", UserWarning)

    class ChatMemberUpdatedExt(ChatMemberUpdated):
        bot: Bot  # marking bot as required for mypy

    class MessageExt(Message):
        bot: Bot  # marking bot as required for mypy

    class MessageFromUser(MessageExt):
        from_user: User  # marking user as required for mypy

    class StartCommandWithDeepLinkObject(CommandObject):
        args: str  # marking args (deep link) as required for mypy
