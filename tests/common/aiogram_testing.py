from collections.abc import Iterable, Sequence
from typing import Any
from unittest.mock import AsyncMock

import pytest
from aiogram import Bot
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.methods import TelegramMethod
from aiogram.types import Update
from pydantic_marshals.contains import TypeChecker, assert_contains
from starlette.testclient import TestClient

from tests.common.assert_contains_ext import assert_nodata_response
from tests.common.id_provider import IDProvider
from tests.common.mock_stack import MockStack


class TelegramBotWebhookDriver:
    def __init__(self, client: TestClient, webhook_url: str) -> None:
        self.client = client
        self.webhook_url = webhook_url

    def feed_update(self, update: Update) -> None:
        assert_nodata_response(
            self.client.post(
                self.webhook_url,
                json=update.model_dump(mode="json", exclude_unset=True),
            )
        )


class MockedBot:
    def __init__(self, bot: Bot, call_mock: AsyncMock) -> None:
        self.bot = bot
        self.call_mock = call_mock
        self.api_call_iterator = self.iter_api_calls()

    @property
    def id(self) -> int:
        return self.bot.id

    def iter_bot_calls(self) -> Iterable[tuple[Sequence[Any], dict[str, Any]]]:
        for mock_call in self.call_mock.mock_calls:
            if len(mock_call) == 2:
                yield mock_call
            elif len(mock_call) == 3 and mock_call[0] == "":
                yield mock_call[1:]

    def iter_api_calls(self) -> Iterable[TelegramMethod[Any]]:
        for args, _ in self.iter_bot_calls():
            assert len(args) == 1
            argument = args[0]
            assert isinstance(argument, TelegramMethod)
            yield argument

    def reset_iteration(self) -> None:
        self.api_call_iterator = self.iter_api_calls()

    def assert_next_api_call(
        self, method: type[TelegramMethod[Any]], data: TypeChecker
    ) -> None:
        argument = next(self.api_call_iterator, None)  # type: ignore[call-overload]
        if argument is None:
            raise AssertionError("Next API call not found")
        assert isinstance(argument, method)
        assert_contains(argument.model_dump(), data)

    def assert_no_more_api_calls(self) -> None:
        assert list(self.api_call_iterator) == []


@pytest.fixture()
def bot_id(id_provider: IDProvider) -> int:
    return id_provider.generate_id()


@pytest.fixture(scope="session")
def bot_token() -> str:
    return "1:a"  # noqa S106  # not a real password, but required


@pytest.fixture(scope="session")
def bot(bot_token: str) -> Bot:
    return Bot(token=bot_token)


@pytest.fixture(autouse=True)
def mocked_bot(mock_stack: MockStack, bot: Bot, bot_id: int) -> MockedBot:
    bot_call_mock = mock_stack.enter_async_mock(Bot, "__call__")
    mock_stack.enter_mock(Bot, "id", property_value=bot_id)
    return MockedBot(bot=bot, call_mock=bot_call_mock)


@pytest.fixture(scope="session")
def base_bot_storage() -> MemoryStorage:
    return MemoryStorage()


@pytest.fixture(autouse=True)
def bot_storage(base_bot_storage: MemoryStorage) -> Iterable[MemoryStorage]:
    yield base_bot_storage
    base_bot_storage.storage.clear()


@pytest.fixture()
def tg_user_id(id_provider: IDProvider) -> int:
    return id_provider.generate_id()


@pytest.fixture()
def tg_chat_id(id_provider: IDProvider) -> int:
    return id_provider.generate_id()
