from collections.abc import AsyncIterator, Iterator
from contextlib import AsyncExitStack

import pytest
from fastapi.testclient import TestClient
from httpx import Headers

from app.common.config import API_KEY, MUB_KEY
from app.common.dependencies.authorization_dep import (
    AUTH_SESSION_ID_HEADER_NAME,
    AUTH_USER_ID_HEADER_NAME,
    AUTH_USERNAME_HEADER_NAME,
    ProxyAuthData,
)
from app.main import app, tmex
from tests.common.polyfactory_ext import BaseModelFactory
from tests.common.tmexio_testing import (
    TMEXIOListenerFactory,
    TMEXIOTestClient,
    TMEXIOTestServer,
)

pytest_plugins = (
    "anyio",
    "tests.common.active_session",
    "tests.common.faker_ext",
    "tests.common.mock_stack",
    "tests.common.respx_ext",
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


@pytest.fixture(scope="session")
def internal_client() -> Iterator[TestClient]:
    with TestClient(app, headers={"X-Api-Key": API_KEY}) as client:
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


@pytest.fixture()
async def tmexio_server() -> AsyncIterator[TMEXIOTestServer]:
    server = TMEXIOTestServer(tmexio=tmex)
    server_mock = server.create_mock()
    server_mock.start()
    yield server
    server_mock.stop()


@pytest.fixture()
async def tmexio_listener_factory(
    tmexio_server: TMEXIOTestServer,
    proxy_auth_data: ProxyAuthData,
) -> AsyncIterator[TMEXIOListenerFactory]:
    async with AsyncExitStack() as stack:

        async def listener_factory(room_name: str | None = None) -> TMEXIOTestClient:
            return await stack.enter_async_context(
                tmexio_server.authorized_listener(
                    proxy_auth_data=proxy_auth_data,
                    room_name=room_name,
                )
            )

        yield listener_factory
