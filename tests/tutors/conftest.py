from collections.abc import AsyncIterator, Sequence
from datetime import datetime, timedelta, timezone
from typing import assert_never
from uuid import uuid4

import pytest
from faker import Faker
from starlette.testclient import TestClient

from app.common.dependencies.authorization_dep import ProxyAuthData
from app.tutors.models.classrooms_db import (
    Classroom,
    ClassroomKind,
    GroupClassroom,
    IndividualClassroom,
)
from app.tutors.models.invitations_db import IndividualInvitation
from app.tutors.models.materials_db import Material
from app.tutors.models.subjects_db import Subject
from app.tutors.models.tutorships_db import Tutorship
from tests.common.active_session import ActiveSession
from tests.common.types import AnyJSON, PytestRequest
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
    client: TestClient, outsider_auth_data: ProxyAuthData
) -> TestClient:
    return TestClient(client.app, headers=outsider_auth_data.as_headers)


@pytest.fixture()
async def individual_invitation(
    active_session: ActiveSession,
    tutor_user_id: int,
) -> IndividualInvitation:
    async with active_session():
        return await IndividualInvitation.create(tutor_id=tutor_user_id)


@pytest.fixture()
async def individual_invitation_data(individual_invitation: Subject) -> AnyJSON:
    return IndividualInvitation.ResponseSchema.model_validate(
        individual_invitation
    ).model_dump(mode="json")


@pytest.fixture()
async def deleted_individual_invitation(
    active_session: ActiveSession,
    individual_invitation: IndividualInvitation,
) -> IndividualInvitation:
    async with active_session():
        await individual_invitation.delete()
    return individual_invitation


@pytest.fixture()
async def deleted_individual_invitation_id(
    deleted_individual_invitation: IndividualInvitation,
) -> int:
    return deleted_individual_invitation.id


@pytest.fixture()
async def deleted_individual_invitation_code(
    deleted_individual_invitation: IndividualInvitation,
) -> str:
    return deleted_individual_invitation.code


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


@pytest.fixture()
async def tutorship(
    active_session: ActiveSession, tutor_user_id: int, student_user_id: int
) -> Tutorship:
    async with active_session():
        return await Tutorship.create(
            tutor_id=tutor_user_id,
            student_id=student_user_id,
        )


@pytest.fixture()
async def tutorship_data(tutorship: Tutorship) -> AnyJSON:
    return Tutorship.ResponseSchema.model_validate(tutorship).model_dump(mode="json")


TUTORSHIPS_LIST_SIZE = 6


async def create_tutorships(
    faker: Faker,
    active_session: ActiveSession,
    user_ids: list[tuple[int, int]],
) -> AsyncIterator[Tutorship]:
    last_created_at: datetime = faker.date_time_between(tzinfo=timezone.utc)
    async with active_session():
        for tutor_id, student_id in user_ids:
            last_created_at = last_created_at - timedelta(minutes=faker.random_int())
            yield await Tutorship.create(
                tutor_id=tutor_id,
                student_id=student_id,
                created_at=last_created_at,
            )


@pytest.fixture()
async def tutor_tutorships(
    faker: Faker,
    active_session: ActiveSession,
    tutor_user_id: int,
) -> AsyncIterator[Sequence[Tutorship]]:
    tutorships: list[Tutorship] = [
        tutorship
        async for tutorship in create_tutorships(
            faker=faker,
            active_session=active_session,
            user_ids=[
                (tutor_user_id, tutor_user_id + i + 1)
                for i in range(TUTORSHIPS_LIST_SIZE)
            ],
        )
    ]

    yield tutorships

    async with active_session():
        for tutorship in tutorships:
            await tutorship.delete()


@pytest.fixture()
async def student_tutorships(
    faker: Faker,
    active_session: ActiveSession,
    student_user_id: int,
) -> AsyncIterator[Sequence[Tutorship]]:
    tutorships: list[Tutorship] = [
        tutorship
        async for tutorship in create_tutorships(
            faker=faker,
            active_session=active_session,
            user_ids=[
                (student_user_id + i + 1, student_user_id)
                for i in range(TUTORSHIPS_LIST_SIZE)
            ],
        )
    ]

    yield tutorships

    async with active_session():
        for tutorship in tutorships:
            await tutorship.delete()


@pytest.fixture()
async def individual_classroom(
    faker: Faker,
    active_session: ActiveSession,
    tutor_user_id: int,
    student_user_id: int,
) -> IndividualClassroom:
    async with active_session():
        return await IndividualClassroom.create(
            **factories.IndividualClassroomInputFactory.build_python(),
            tutor_id=tutor_user_id,
            student_id=student_user_id,
            tutor_name=faker.name(),
            student_name=faker.name(),
        )


@pytest.fixture()
async def individual_classroom_tutor_data(
    individual_classroom: IndividualClassroom,
) -> AnyJSON:
    return IndividualClassroom.TutorResponseSchema.model_validate(
        individual_classroom
    ).model_dump(mode="json", by_alias=True)


@pytest.fixture()
async def group_classroom(
    active_session: ActiveSession, tutor_user_id: int
) -> GroupClassroom:
    async with active_session():
        return await GroupClassroom.create(
            **factories.GroupClassroomInputFactory.build_python(),
            tutor_id=tutor_user_id,
        )


@pytest.fixture()
async def group_classroom_tutor_data(group_classroom: GroupClassroom) -> AnyJSON:
    return GroupClassroom.TutorResponseSchema.model_validate(
        group_classroom
    ).model_dump(mode="json", by_alias=True)


@pytest.fixture(params=[ClassroomKind.INDIVIDUAL, ClassroomKind.GROUP])
async def parametrized_classroom_kind(
    request: PytestRequest[ClassroomKind],
) -> ClassroomKind:
    return request.param


@pytest.fixture()
async def any_classroom(
    individual_classroom: IndividualClassroom,
    group_classroom: GroupClassroom,
    parametrized_classroom_kind: ClassroomKind,
) -> Classroom:
    match parametrized_classroom_kind:
        case ClassroomKind.INDIVIDUAL:
            return individual_classroom
        case ClassroomKind.GROUP:
            return group_classroom
        case _:
            assert_never(parametrized_classroom_kind)


@pytest.fixture()
async def any_classroom_tutor_data(
    individual_classroom_tutor_data: AnyJSON,
    group_classroom_tutor_data: AnyJSON,
    parametrized_classroom_kind: ClassroomKind,
) -> AnyJSON:
    match parametrized_classroom_kind:
        case ClassroomKind.INDIVIDUAL:
            return individual_classroom_tutor_data
        case ClassroomKind.GROUP:
            return group_classroom_tutor_data
        case _:
            assert_never(parametrized_classroom_kind)
