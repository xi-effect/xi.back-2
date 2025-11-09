from collections.abc import Iterator

import pytest
from faker import Faker
from respx import MockRouter, mock

from app.pochta.dependencies.unisender_go_dep import unisender_go_client_manager


@pytest.fixture()
def unisender_go_api_key(faker: Faker) -> str:
    return faker.uuid4()


@pytest.fixture()
def unisender_go_mock(unisender_go_api_key: str) -> Iterator[MockRouter]:
    unisender_go_client_manager.unisender_go_api_key = unisender_go_api_key

    mock_router: MockRouter = mock(base_url="https://go2.unisender.ru/ru/transactional")
    with mock_router:
        yield mock_router

    unisender_go_client_manager.unisender_go_api_key = None
    unisender_go_client_manager.unisender_go_client = None
