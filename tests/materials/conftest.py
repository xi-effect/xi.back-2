from uuid import uuid4

import pytest
from faker import Faker
from starlette.testclient import TestClient

from app.common.dependencies.authorization_dep import ProxyAuthData
from app.materials.models.materials_db import ClassroomMaterial, TutorMaterial
from tests.common.active_session import ActiveSession
from tests.common.types import AnyJSON
from tests.factories import ProxyAuthDataFactory
from tests.materials import factories


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
def student_auth_data() -> ProxyAuthData:
    return ProxyAuthDataFactory.build()


@pytest.fixture()
def student_user_id(student_auth_data: ProxyAuthData) -> int:
    return student_auth_data.user_id


@pytest.fixture()
def student_client(client: TestClient, student_auth_data: ProxyAuthData) -> TestClient:
    return TestClient(client.app, headers=student_auth_data.as_headers)


@pytest.fixture()
def outsider_auth_data() -> ProxyAuthData:
    return ProxyAuthDataFactory.build()


@pytest.fixture()
def outsider_client(
    client: TestClient,
    outsider_auth_data: ProxyAuthData,
) -> TestClient:
    return TestClient(client.app, headers=outsider_auth_data.as_headers)


@pytest.fixture()
async def tutor_material(
    active_session: ActiveSession,
    tutor_user_id: int,
) -> TutorMaterial:
    async with active_session():
        return await TutorMaterial.create(
            **factories.TutorMaterialInputFactory.build_python(),
            tutor_id=tutor_user_id,
            access_group_id=uuid4(),
            content_id=uuid4(),
        )


@pytest.fixture()
async def tutor_material_data(tutor_material: TutorMaterial) -> AnyJSON:
    return TutorMaterial.ResponseSchema.model_validate(tutor_material).model_dump(
        mode="json"
    )


@pytest.fixture()
async def deleted_tutor_material_id(
    active_session: ActiveSession,
    tutor_material: TutorMaterial,
) -> int:
    async with active_session():
        await tutor_material.delete()
    return tutor_material.id


@pytest.fixture()
async def classroom_id(faker: Faker) -> int:
    return faker.random_int()


@pytest.fixture()
async def classroom_material(
    active_session: ActiveSession,
    classroom_id: int,
) -> ClassroomMaterial:
    async with active_session():
        return await ClassroomMaterial.create(
            **factories.ClassroomMaterialInputFactory.build_python(),
            classroom_id=classroom_id,
            access_group_id=uuid4(),
            content_id=uuid4(),
        )


@pytest.fixture()
async def classroom_material_data(classroom_material: ClassroomMaterial) -> AnyJSON:
    return ClassroomMaterial.ResponseSchema.model_validate(
        classroom_material
    ).model_dump(mode="json")


@pytest.fixture()
async def deleted_classroom_material_id(
    active_session: ActiveSession,
    classroom_material: ClassroomMaterial,
) -> int:
    async with active_session():
        await classroom_material.delete()
    return classroom_material.id
