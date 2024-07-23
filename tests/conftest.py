from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from httpx import Headers

from app.common.config import MUB_KEY
from app.common.dependencies.authorization_dep import (
    AUTH_SESSION_ID_HEADER_NAME,
    AUTH_USER_ID_HEADER_NAME,
    AUTH_USERNAME_HEADER_NAME,
    ProxyAuthData,
)
from app.main import app
from tests.common.polyfactory_ext import BaseModelFactory

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
def authorized_client_base() -> Iterator[TestClient]:
    with TestClient(app) as client:
        yield client


class ProxyAuthDataFactory(BaseModelFactory[ProxyAuthData]):
    __model__ = ProxyAuthData


@pytest.fixture()
def proxy_auth_data() -> ProxyAuthData:
    return ProxyAuthDataFactory.build()


@pytest.fixture()
def authorized_client(
    authorized_client_base: TestClient,
    proxy_auth_data: ProxyAuthData,
) -> Iterator[TestClient]:
    authorized_client_base.headers = Headers(
        {
            AUTH_SESSION_ID_HEADER_NAME: str(proxy_auth_data.session_id),
            AUTH_USER_ID_HEADER_NAME: str(proxy_auth_data.user_id),
            AUTH_USERNAME_HEADER_NAME: proxy_auth_data.username,
        }
    )
    yield authorized_client_base
    authorized_client_base.headers = Headers()


@pytest.fixture(scope="session")
def mub_client() -> Iterator[TestClient]:
    with TestClient(app, headers={"X-MUB-Secret": MUB_KEY}) as client:
        yield client
