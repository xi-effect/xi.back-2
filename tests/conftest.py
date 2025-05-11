from collections.abc import AsyncIterator, Iterator
from contextlib import AsyncExitStack

import pytest
from faker import Faker
from faker_file.providers.pdf_file.generators.pil_generator import (  # type: ignore[import-untyped]
    PilPdfGenerator,
)
from fastapi.testclient import TestClient

from app.common.config import settings
from app.common.dependencies.authorization_dep import ProxyAuthData
from app.main import app, tmex
from tests import factories
from tests.common.polyfactory_ext import BaseModelFactory
from tests.common.tmexio_testing import (
    TMEXIOListenerFactory,
    TMEXIOTestClient,
    TMEXIOTestServer,
)
from tests.common.types import AnyJSON

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
    with TestClient(app, base_url=f"http://{settings.cookie_domain}") as client:
        yield client


@pytest.fixture()
def mub_client(client: TestClient) -> TestClient:
    return TestClient(
        client.app,
        base_url=f"http://{settings.cookie_domain}",
        headers={"X-MUB-Secret": settings.mub_key},
    )


@pytest.fixture()
def internal_client(client: TestClient) -> TestClient:
    return TestClient(client.app, headers={"X-Api-Key": settings.api_key})


class ProxyAuthDataFactory(BaseModelFactory[ProxyAuthData]):
    __model__ = ProxyAuthData


@pytest.fixture()
def proxy_auth_data() -> ProxyAuthData:
    return ProxyAuthDataFactory.build()


@pytest.fixture()
def authorized_client(client: TestClient, proxy_auth_data: ProxyAuthData) -> TestClient:
    return TestClient(client.app, headers=proxy_auth_data.as_headers)


@pytest.fixture()
def authorized_internal_client(
    proxy_auth_data: ProxyAuthData, client: TestClient
) -> TestClient:
    return TestClient(
        client.app,
        headers={
            **proxy_auth_data.as_headers,
            "X-Api-Key": settings.api_key,
        },
    )


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


@pytest.fixture()
async def pdf_data(faker: Faker) -> tuple[str, bytes, str]:
    return (
        faker.file_name(extension="pdf"),
        faker.pdf_file(raw=True, pdf_generator_cls=PilPdfGenerator),
        "application/pdf",
    )


@pytest.fixture()
def vacancy_form_data() -> AnyJSON:
    return factories.VacancyFormWithMessageFactory.build_json()
