from collections.abc import AsyncIterator, Iterator
from datetime import datetime, timedelta, timezone
from typing import assert_never

import pytest
from faker import Faker
from starlette.testclient import TestClient

from app.tutors.models.classrooms_db import (
    AnyClassroom,
    GroupClassroom,
    IndividualClassroom,
)
from app.tutors.models.enrollments_db import Enrollment
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_response
from tests.common.types import AnyJSON
from tests.common.utils import remove_none_values
from tests.tutors import factories

pytestmark = pytest.mark.anyio

CLASSROOMS_LIST_SIZE = 8


async def create_tutor_classrooms(
    faker: Faker,
    active_session: ActiveSession,
    tutor_user_id: int,
) -> AsyncIterator[AnyClassroom]:
    last_created_at: datetime = faker.date_time_between(tzinfo=timezone.utc)
    async with active_session():
        for i in range(CLASSROOMS_LIST_SIZE):
            if i % 2 == 0:
                yield await IndividualClassroom.create(
                    **factories.IndividualClassroomInputFactory.build_python(),
                    tutor_id=tutor_user_id,
                    student_id=tutor_user_id + i + 1,
                    tutor_name=faker.name(),
                    student_name=faker.name(),
                    created_at=last_created_at,
                )
            else:
                yield await GroupClassroom.create(
                    **factories.GroupClassroomInputFactory.build_python(),
                    tutor_id=tutor_user_id,
                    created_at=last_created_at,
                )
            last_created_at -= timedelta(minutes=faker.random_int(min=1))


@pytest.fixture()
async def tutor_classrooms(
    active_session: ActiveSession,
    faker: Faker,
    tutor_user_id: int,
) -> AsyncIterator[list[AnyClassroom]]:
    classrooms: list[AnyClassroom] = [
        classroom
        async for classroom in create_tutor_classrooms(
            faker=faker,
            active_session=active_session,
            tutor_user_id=tutor_user_id,
        )
    ]

    yield classrooms

    async with active_session():
        for classroom in classrooms:
            await classroom.delete()


def convert_tutor_classrooms(tutor_classrooms: list[AnyClassroom]) -> Iterator[AnyJSON]:
    for classroom in tutor_classrooms:
        match classroom:
            case IndividualClassroom():
                yield IndividualClassroom.TutorResponseSchema.model_validate(
                    classroom, from_attributes=True
                ).model_dump(mode="json", by_alias=True)
            case GroupClassroom():
                yield GroupClassroom.TutorResponseSchema.model_validate(
                    classroom, from_attributes=True
                ).model_dump(mode="json", by_alias=True)
            case _:
                assert_never(classroom)


@pytest.mark.parametrize(
    ("offset", "limit"),
    [
        pytest.param(0, CLASSROOMS_LIST_SIZE, id="start_to_end"),
        pytest.param(0, CLASSROOMS_LIST_SIZE // 2, id="start_to_middle"),
        pytest.param(
            CLASSROOMS_LIST_SIZE // 2,
            CLASSROOMS_LIST_SIZE,
            id="middle_to_end",
        ),
    ],
)
async def test_tutor_classrooms_listing(
    tutor_client: TestClient,
    tutor_classrooms: list[AnyClassroom],
    offset: int,
    limit: int,
) -> None:
    assert_response(
        tutor_client.get(
            "/api/protected/tutor-service/roles/tutor/classrooms/",
            params=remove_none_values(
                {
                    "created_before": (
                        None
                        if offset == 0
                        else tutor_classrooms[offset - 1].created_at.isoformat()
                    ),
                    "limit": limit,
                }
            ),
        ),
        expected_json=list(convert_tutor_classrooms(tutor_classrooms=tutor_classrooms))[
            offset:limit
        ],
    )


async def create_student_classrooms(
    faker: Faker,
    active_session: ActiveSession,
    student_user_id: int,
) -> AsyncIterator[AnyClassroom]:
    last_created_at: datetime = faker.date_time_between(tzinfo=timezone.utc)
    async with active_session():
        for i in range(CLASSROOMS_LIST_SIZE):
            if i % 2 == 0:
                yield await IndividualClassroom.create(
                    **factories.IndividualClassroomInputFactory.build_python(),
                    tutor_id=student_user_id + i + 1,
                    student_id=student_user_id,
                    tutor_name=faker.name(),
                    student_name=faker.name(),
                    created_at=last_created_at,
                )
            else:
                group_classroom = await GroupClassroom.create(
                    **factories.GroupClassroomInputFactory.build_python(),
                    tutor_id=student_user_id + i + 1,
                    created_at=last_created_at,
                )
                await Enrollment.create(
                    group_classroom_id=group_classroom.id,
                    student_id=student_user_id,
                )
                yield group_classroom
            last_created_at -= timedelta(minutes=faker.random_int(min=1))


@pytest.fixture()
async def student_classrooms(
    active_session: ActiveSession,
    faker: Faker,
    student_user_id: int,
) -> AsyncIterator[list[AnyClassroom]]:
    classrooms: list[AnyClassroom] = [
        classroom
        async for classroom in create_student_classrooms(
            faker=faker,
            active_session=active_session,
            student_user_id=student_user_id,
        )
    ]

    yield classrooms

    async with active_session():
        for classroom in classrooms:
            await classroom.delete()


def convert_student_classrooms(
    student_classrooms: list[AnyClassroom],
) -> Iterator[AnyJSON]:
    for classroom in student_classrooms:
        match classroom:
            case IndividualClassroom():
                yield IndividualClassroom.StudentResponseSchema.model_validate(
                    classroom, from_attributes=True
                ).model_dump(mode="json", by_alias=True)
            case GroupClassroom():
                yield GroupClassroom.StudentResponseSchema.model_validate(
                    classroom, from_attributes=True
                ).model_dump(mode="json", by_alias=True)
            case _:
                assert_never(classroom)


@pytest.mark.parametrize(
    ("offset", "limit"),
    [
        pytest.param(0, CLASSROOMS_LIST_SIZE, id="start_to_end"),
        pytest.param(0, CLASSROOMS_LIST_SIZE // 2, id="start_to_middle"),
        pytest.param(
            CLASSROOMS_LIST_SIZE // 2,
            CLASSROOMS_LIST_SIZE,
            id="middle_to_end",
        ),
    ],
)
async def test_student_classrooms_listing(
    student_client: TestClient,
    student_classrooms: list[AnyClassroom],
    offset: int,
    limit: int,
) -> None:
    assert_response(
        student_client.get(
            "/api/protected/tutor-service/roles/student/classrooms/",
            params=remove_none_values(
                {
                    "created_before": (
                        None
                        if offset == 0
                        else student_classrooms[offset - 1].created_at.isoformat()
                    ),
                    "limit": limit,
                }
            ),
        ),
        expected_json=list(
            convert_student_classrooms(student_classrooms=student_classrooms)
        )[offset:limit],
    )
