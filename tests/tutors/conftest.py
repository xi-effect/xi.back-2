from uuid import uuid4

import pytest
from starlette.testclient import TestClient

from app.common.dependencies.authorization_dep import ProxyAuthData
from app.tutors.models.invitations_db import Invitation
from app.tutors.models.materials_db import Material
from app.tutors.models.subjects_db import Subject
from tests.common.active_session import ActiveSession
from tests.common.types import AnyJSON
from tests.factories import ProxyAuthDataFactory
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
async def invitation(
    active_session: ActiveSession,
    tutor_user_id: int,
) -> Invitation:
    async with active_session():
        return await Invitation.create(tutor_id=tutor_user_id)


@pytest.fixture()
async def invitation_data(invitation: Subject) -> AnyJSON:
    return Invitation.ResponseSchema.model_validate(invitation).model_dump(mode="json")


@pytest.fixture()
async def deleted_invitation_id(
    active_session: ActiveSession,
    invitation: Invitation,
) -> int:
    async with active_session():
        await invitation.delete()
    return invitation.id


@pytest.fixture()
async def subject(active_session: ActiveSession, tutor_user_id: int) -> Subject:
    async with active_session():
        return await Subject.create(
            **factories.SubjectInputFactory.build_python(), tutor_id=tutor_user_id
        )


@pytest.fixture()
async def subject_data(subject: Subject) -> AnyJSON:
    return Subject.ResponseMUBSchema.model_validate(subject).model_dump(mode="json")


@pytest.fixture()
async def deleted_subject_id(active_session: ActiveSession, subject: Subject) -> int:
    async with active_session():
        await subject.delete()
    return subject.id


@pytest.fixture()
async def material(active_session: ActiveSession, tutor_user_id: int) -> Material:
    async with active_session():
        return await Material.create(
            **factories.MaterialInputFactory.build_python(),
            tutor_id=tutor_user_id,
            ydoc_id=str(uuid4()),
        )


@pytest.fixture()
async def material_data(material: Material) -> AnyJSON:
    return Material.ResponseSchema.model_validate(material).model_dump(mode="json")


@pytest.fixture()
async def deleted_material_id(active_session: ActiveSession, material: Material) -> int:
    async with active_session():
        await material.delete()
    return material.id
