from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.common.config import MUB_KEY
from app.main import app

pytest_plugins = (
    "anyio",
    "tests.common.active_session",
    "tests.common.faker_ext",
    "tests.common.mock_stack",
)


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session")
def client() -> Iterator[TestClient]:
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="session")
def mub_client() -> Iterator[TestClient]:
    with TestClient(app, headers={"X-MUB-Secret": MUB_KEY}) as client:
        yield client
