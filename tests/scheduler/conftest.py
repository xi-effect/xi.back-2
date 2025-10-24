import pytest
from faker import Faker
from starlette.testclient import TestClient

from app.common.dependencies.authorization_dep import ProxyAuthData
from app.scheduler.models.events_db import ClassroomEvent
from tests.common.active_session import ActiveSession
from tests.common.types import AnyJSON
from tests.factories import ProxyAuthDataFactory
from tests.scheduler import factories


@pytest.fixture()
def tutor_auth_data() -> ProxyAuthData:
    return ProxyAuthDataFactory.build()


@pytest.fixture()
def tutor_client(client: TestClient, tutor_auth_data: ProxyAuthData) -> TestClient:
    return TestClient(client.app, headers=tutor_auth_data.as_headers)


@pytest.fixture()
def student_auth_data() -> ProxyAuthData:
    return ProxyAuthDataFactory.build()


@pytest.fixture()
def student_client(client: TestClient, student_auth_data: ProxyAuthData) -> TestClient:
    return TestClient(client.app, headers=student_auth_data.as_headers)


@pytest.fixture()
def classroom_id(faker: Faker) -> int:
    return faker.random_int(1, 1000)


@pytest.fixture()
def other_classroom_id(faker: Faker, classroom_id: int) -> int:
    return faker.random_int(classroom_id + 1, classroom_id + 1000)


@pytest.fixture()
async def classroom_event(
    active_session: ActiveSession, classroom_id: int
) -> ClassroomEvent:
    async with active_session():
        return await ClassroomEvent.create(
            **factories.ClassroomEventInputFactory.build_python(),
            classroom_id=classroom_id,
        )


@pytest.fixture()
def classroom_event_data(classroom_event: ClassroomEvent) -> AnyJSON:
    return ClassroomEvent.ResponseSchema.model_validate(
        classroom_event, from_attributes=True
    ).model_dump(mode="json")


@pytest.fixture()
async def deleted_classroom_event_id(
    active_session: ActiveSession,
    classroom_event: ClassroomEvent,
) -> int:
    async with active_session():
        await classroom_event.delete()
    return classroom_event.id
