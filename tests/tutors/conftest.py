import pytest
from starlette.testclient import TestClient

from app.common.dependencies.authorization_dep import ProxyAuthData
from app.tutors.models.materials_db import Material
from tests.common.active_session import ActiveSession
from tests.common.types import AnyJSON
from tests.conftest import ProxyAuthDataFactory
from tests.tutors import factories


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


@pytest.fixture()
async def material(active_session: ActiveSession, tutor_user_id: int) -> Material:
    async with active_session():
        return await Material.create(
            **factories.MaterialInputFactory.build_python(), tutor_id=tutor_user_id
        )


@pytest.fixture()
async def material_data(material: Material) -> AnyJSON:
    return Material.ResponseSchema.model_validate(material).model_dump(mode="json")


@pytest.fixture()
async def deleted_material_id(active_session: ActiveSession, material: Material) -> int:
    async with active_session():
        await material.delete()
    return material.id
