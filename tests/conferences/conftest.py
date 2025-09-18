from typing import Literal

import pytest
from faker import Faker
from livekit.protocol.models import Room
from starlette.testclient import TestClient

from app.common.dependencies.authorization_dep import ProxyAuthData
from tests.common.types import PytestRequest
from tests.factories import ProxyAuthDataFactory


@pytest.fixture()
def outsider_auth_data() -> ProxyAuthData:
    return ProxyAuthDataFactory.build()


@pytest.fixture()
def outsider_client(
    client: TestClient, outsider_auth_data: ProxyAuthData
) -> TestClient:
    return TestClient(client.app, headers=outsider_auth_data.as_headers)


@pytest.fixture()
def outsider_user_id(outsider_auth_data: ProxyAuthData) -> int:
    return outsider_auth_data.user_id


ClassroomRoleType = Literal["tutor", "student"]


@pytest.fixture(params=["tutor", "student"])
def parametrized_classroom_role(
    request: PytestRequest[ClassroomRoleType],
) -> ClassroomRoleType:
    return request.param


@pytest.fixture()
async def classroom_id(faker: Faker) -> int:
    return faker.random_int()


@pytest.fixture()
async def classroom_conference_room_name(classroom_id: int) -> str:
    return f"classroom-{classroom_id}"


@pytest.fixture()
async def classroom_conference_room(classroom_conference_room_name: str) -> Room:
    return Room(name=classroom_conference_room_name)
