import random
from collections.abc import AsyncIterator, Iterator
from datetime import datetime, timedelta, timezone
from itertools import product
from typing import assert_never

import pytest
from faker import Faker
from starlette.testclient import TestClient

from app.classrooms.models.classrooms_db import (
    AnyClassroom,
    ClassroomCursorSchema,
    ClassroomFiltersSchema,
    ClassroomKind,
    ClassroomSearchRequestSchema,
    ClassroomStatus,
    GroupClassroom,
    IndividualClassroom,
)
from app.classrooms.models.enrollments_db import Enrollment
from tests.classrooms import factories
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_response
from tests.common.types import AnyJSON
from tests.common.utils import remove_none_values

pytestmark = pytest.mark.anyio

CLASSROOMS_STATUSES = list(ClassroomStatus)
CLASSROOMS_KINDS = list(ClassroomKind)
CLASSROOMS_SUBJECT_IDS = [*random.sample(range(1, 999), k=2), None]
CLASSROOMS_LIST_SIZE = (
    len(CLASSROOMS_SUBJECT_IDS) * len(CLASSROOMS_KINDS) * len(CLASSROOMS_STATUSES)
)


async def create_tutor_classrooms(
    faker: Faker,
    active_session: ActiveSession,
    tutor_user_id: int,
) -> AsyncIterator[AnyClassroom]:
    last_created_at: datetime = faker.date_time_between(tzinfo=timezone.utc)
    async with active_session():
        for i in range(CLASSROOMS_LIST_SIZE):
            kind = CLASSROOMS_KINDS[
                i // (CLASSROOMS_LIST_SIZE // 2) % len(CLASSROOMS_KINDS)
            ]
            match kind:
                case ClassroomKind.INDIVIDUAL:
                    yield await IndividualClassroom.create(
                        **factories.IndividualClassroomInputFactory.build_python(
                            subject_id=CLASSROOMS_SUBJECT_IDS[
                                i % len(CLASSROOMS_SUBJECT_IDS)
                            ],
                        ),
                        status=CLASSROOMS_STATUSES[i % len(CLASSROOMS_STATUSES)],
                        tutor_id=tutor_user_id,
                        student_id=tutor_user_id + i + 1,
                        tutor_name=faker.name(),
                        student_name=faker.name(),
                        created_at=last_created_at,
                    )
                case ClassroomKind.GROUP:
                    yield await GroupClassroom.create(
                        **factories.GroupClassroomInputFactory.build_python(
                            subject_id=CLASSROOMS_SUBJECT_IDS[
                                i % len(CLASSROOMS_SUBJECT_IDS)
                            ],
                        ),
                        status=CLASSROOMS_STATUSES[i % len(CLASSROOMS_STATUSES)],
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


classroom_requests_parametrization_old = pytest.mark.parametrize(
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

classroom_requests_parametrization = pytest.mark.parametrize(
    ("offset", "limit"),
    [
        pytest.param(None, CLASSROOMS_LIST_SIZE, id="start_to_end"),
        pytest.param(None, CLASSROOMS_LIST_SIZE // 2, id="start_to_middle"),
        pytest.param(
            CLASSROOMS_LIST_SIZE // 2,
            CLASSROOMS_LIST_SIZE,
            id="middle_to_end",
        ),
    ],
)


@classroom_requests_parametrization_old
async def test_tutor_classrooms_listing_old(
    tutor_client: TestClient,
    tutor_classrooms: list[AnyClassroom],
    offset: int,
    limit: int,
) -> None:
    assert_response(
        tutor_client.get(
            "/api/protected/classroom-service/roles/tutor/classrooms/",
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


classroom_requests_filter = pytest.mark.parametrize(
    ("kinds", "statuses", "subject_ids"),
    [
        *[
            pytest.param(kind, status, subject_id, id=f"{kind}_{status}_{subject_id}")
            for kind, status, subject_id in product(
                (None, {ClassroomKind.INDIVIDUAL.value}),
                (None, {ClassroomStatus.ACTIVE.value}),
                (None, {CLASSROOMS_SUBJECT_IDS[0]}),
            )
        ],
        pytest.param(None, set(CLASSROOMS_STATUSES[:2]), None, id="multiple_statuses"),
        pytest.param(set(CLASSROOMS_KINDS[:2]), None, None, id="multiple_kinds"),
        pytest.param(
            None, None, set(CLASSROOMS_SUBJECT_IDS[:2]), id="multiple_subject_ids"
        ),
        pytest.param(set(CLASSROOMS_KINDS), None, None, id="all_kinds"),
        pytest.param(None, set(CLASSROOMS_STATUSES), None, id="all_statuses"),
        pytest.param(
            set(CLASSROOMS_KINDS),
            set(CLASSROOMS_STATUSES),
            set(CLASSROOMS_SUBJECT_IDS[:2]),
            id="all_filter",
        ),
    ],
)


@classroom_requests_filter
@classroom_requests_parametrization
async def test_tutor_classrooms_listing(
    tutor_client: TestClient,
    tutor_classrooms: list[AnyClassroom],
    kinds: set[ClassroomKind] | None,
    statuses: set[ClassroomStatus] | None,
    subject_ids: set[int] | None,
    offset: int | None,
    limit: int,
) -> None:
    cursor = None if offset is None else tutor_classrooms[offset]
    filtered_tutor_classroom = [
        classroom
        for classroom in tutor_classrooms
        if all(
            (
                statuses is None or classroom.status in statuses,
                kinds is None or classroom.kind in kinds,
                subject_ids is None or classroom.subject_id in subject_ids,
                cursor is None or classroom.created_at < cursor.created_at,
            )
        )
    ]

    assert_response(
        tutor_client.post(
            "/api/protected/classroom-service/roles/tutor/classrooms/searches/",
            json=remove_none_values(
                ClassroomSearchRequestSchema(
                    filters=ClassroomFiltersSchema(
                        statuses=statuses,
                        kinds=kinds,
                        subject_ids=subject_ids,
                    ),
                    cursor=(
                        None
                        if cursor is None
                        else ClassroomCursorSchema(created_at=cursor.created_at)
                    ),
                    limit=limit,
                ).model_dump(mode="json")
            ),
        ),
        expected_json=list(convert_tutor_classrooms(filtered_tutor_classroom))[:limit],
    )


async def create_student_classrooms(
    faker: Faker,
    active_session: ActiveSession,
    student_user_id: int,
) -> AsyncIterator[AnyClassroom]:
    last_created_at: datetime = faker.date_time_between(tzinfo=timezone.utc)
    async with active_session():
        for i in range(CLASSROOMS_LIST_SIZE):
            kind = CLASSROOMS_KINDS[
                i
                // (CLASSROOMS_LIST_SIZE // len(CLASSROOMS_KINDS))
                % len(CLASSROOMS_KINDS)
            ]
            match kind:
                case ClassroomKind.INDIVIDUAL:
                    yield await IndividualClassroom.create(
                        **factories.IndividualClassroomInputFactory.build_python(
                            subject_id=CLASSROOMS_SUBJECT_IDS[
                                (i // len(CLASSROOMS_STATUSES))
                                % len(CLASSROOMS_SUBJECT_IDS)
                            ],
                        ),
                        status=CLASSROOMS_STATUSES[i % len(CLASSROOMS_STATUSES)],
                        tutor_id=student_user_id + i + 1,
                        student_id=student_user_id,
                        tutor_name=faker.name(),
                        student_name=faker.name(),
                        created_at=last_created_at,
                    )
                case ClassroomKind.GROUP:
                    group_classroom = await GroupClassroom.create(
                        **factories.GroupClassroomInputFactory.build_python(
                            subject_id=CLASSROOMS_SUBJECT_IDS[
                                (i // len(CLASSROOMS_STATUSES))
                                % len(CLASSROOMS_SUBJECT_IDS)
                            ],
                        ),
                        status=CLASSROOMS_STATUSES[i % len(CLASSROOMS_STATUSES)],
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


@classroom_requests_parametrization_old
async def test_student_classrooms_listing_old(
    student_client: TestClient,
    student_classrooms: list[AnyClassroom],
    offset: int,
    limit: int,
) -> None:
    assert_response(
        student_client.get(
            "/api/protected/classroom-service/roles/student/classrooms/",
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


@classroom_requests_filter
@classroom_requests_parametrization
async def test_student_classrooms_listing(
    student_client: TestClient,
    student_classrooms: list[AnyClassroom],
    kinds: set[ClassroomKind] | None,
    statuses: set[ClassroomStatus] | None,
    subject_ids: set[int] | None,
    offset: int,
    limit: int,
) -> None:
    cursor = None if offset is None else student_classrooms[offset]
    filtered_student_classroom = [
        classroom
        for classroom in student_classrooms
        if all(
            (
                statuses is None or classroom.status in statuses,
                kinds is None or classroom.kind in kinds,
                subject_ids is None or classroom.subject_id in subject_ids,
                cursor is None or classroom.created_at < cursor.created_at,
            )
        )
    ]

    assert_response(
        student_client.post(
            "/api/protected/classroom-service/roles/student/classrooms/searches/",
            json=remove_none_values(
                ClassroomSearchRequestSchema(
                    filters=ClassroomFiltersSchema(
                        statuses=statuses,
                        kinds=kinds,
                        subject_ids=subject_ids,
                    ),
                    cursor=(
                        None
                        if cursor is None
                        else ClassroomCursorSchema(created_at=cursor.created_at)
                    ),
                    limit=limit,
                ).model_dump(mode="json")
            ),
        ),
        expected_json=list(convert_student_classrooms(filtered_student_classroom))[
            :limit
        ],
    )
