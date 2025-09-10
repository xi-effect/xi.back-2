import pytest
from starlette.testclient import TestClient

from app.common.dependencies.authorization_dep import ProxyAuthData
from tests.factories import ProxyAuthDataFactory


@pytest.fixture()
def tutor_auth_data() -> ProxyAuthData:
    return ProxyAuthDataFactory.build()


@pytest.fixture()
def tutor_user_id(tutor_auth_data: ProxyAuthData) -> int:
    return tutor_auth_data.user_id


@pytest.fixture()
def tutor_client(client: TestClient, tutor_auth_data: ProxyAuthData) -> TestClient:
    return TestClient(client.app, headers=tutor_auth_data.as_headers)


@pytest.fixture()
def outsider_auth_data() -> ProxyAuthData:
    return ProxyAuthDataFactory.build()


@pytest.fixture()
def outsider_client(
    client: TestClient, outsider_auth_data: ProxyAuthData
) -> TestClient:
    return TestClient(client.app, headers=outsider_auth_data.as_headers)
