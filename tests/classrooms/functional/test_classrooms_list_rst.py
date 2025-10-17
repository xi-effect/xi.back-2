import random
from collections.abc import AsyncIterator, Iterator
from datetime import datetime, timedelta, timezone
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
CLASSROOMS_SUBJECT_IDS = range(1, 5)
CLASSROOMS_LIST_SIZE = 2 * len(CLASSROOMS_KINDS) * len(CLASSROOMS_STATUSES)


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
            else:
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


def apply_filters_to_classrooms(
    classrooms: list[AnyClassroom],
    statuses: set[str] | None = None,
    kinds: set[str] | None = None,
    subject_ids: set[int] | None = None,
) -> list[AnyClassroom]:
    return [
        classroom
        for classroom in classrooms
        if (statuses is None or classroom.status in statuses)  # noqa: WPS222
        and (kinds is None or classroom.kind in kinds)
        and (subject_ids is None or classroom.subject_id in subject_ids)
    ]


classroom_requests_parametrization = pytest.mark.parametrize(
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


@classroom_requests_parametrization
async def test_tutor_classrooms_listing(
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


classroom_filters_parametrization = pytest.mark.parametrize(
    "classroom_filters_schema",
    [
        pytest.param(ClassroomFiltersSchema(), id="no_filters"),
        pytest.param(
            ClassroomFiltersSchema(statuses={random.choice(CLASSROOMS_STATUSES)}),
            id="filter_by_statuses",
        ),
        pytest.param(
            ClassroomFiltersSchema(kinds={random.choice(CLASSROOMS_KINDS)}),
            id="filter_by_kind",
        ),
        pytest.param(
            ClassroomFiltersSchema(subject_ids={random.choice(CLASSROOMS_SUBJECT_IDS)}),
            id="filter_by_subject_ids",
        ),
        pytest.param(
            ClassroomFiltersSchema(
                subject_ids={random.choice(CLASSROOMS_SUBJECT_IDS)},
                kinds={random.choice(CLASSROOMS_KINDS)},
                statuses={random.choice(CLASSROOMS_STATUSES)},
            ),
            id="filter_by_everything",
        ),
        pytest.param(
            ClassroomFiltersSchema(
                statuses={
                    random.choice(CLASSROOMS_STATUSES[: len(CLASSROOMS_STATUSES) // 2]),
                    random.choice(CLASSROOMS_STATUSES[len(CLASSROOMS_STATUSES) // 2 :]),
                },
            ),
            id="multiple_choice_by_statuses",
        ),
        pytest.param(
            ClassroomFiltersSchema(
                subject_ids={
                    random.choice(
                        CLASSROOMS_SUBJECT_IDS[: len(CLASSROOMS_SUBJECT_IDS) // 2]
                    ),
                    random.choice(
                        CLASSROOMS_SUBJECT_IDS[len(CLASSROOMS_SUBJECT_IDS) // 2 :]
                    ),
                }
            ),
            id="multiple_choice_by_subject_ids",
        ),
        pytest.param(
            ClassroomFiltersSchema(kinds=set(CLASSROOMS_KINDS)),
            id="multiple_choice_by_kinds",
        ),
    ],
)


@classroom_filters_parametrization
@classroom_requests_parametrization
async def test_tutor_classrooms_listing_search(
    tutor_client: TestClient,
    tutor_classrooms: list[AnyClassroom],
    classroom_filters_schema: ClassroomFiltersSchema,
    offset: int,
    limit: int,
) -> None:
    filtered_tutor_classroom: list[AnyClassroom] = apply_filters_to_classrooms(
        classrooms=tutor_classrooms[offset:],
        **classroom_filters_schema.model_dump(),
    )

    assert_response(
        tutor_client.post(
            "/api/protected/classroom-service/roles/tutor/classrooms/searches/",
            json=remove_none_values(
                ClassroomSearchRequestSchema(
                    filters=classroom_filters_schema,
                    cursor=(
                        None
                        if offset == 0
                        else ClassroomCursorSchema(
                            created_at=tutor_classrooms[offset - 1].created_at
                        )
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
            if i % 2 == 0:
                yield await IndividualClassroom.create(
                    **factories.IndividualClassroomInputFactory.build_python(
                        subject_id=CLASSROOMS_SUBJECT_IDS[
                            i % len(CLASSROOMS_SUBJECT_IDS)
                        ],
                    ),
                    status=CLASSROOMS_STATUSES[i % len(CLASSROOMS_STATUSES)],
                    tutor_id=student_user_id + i + 1,
                    student_id=student_user_id,
                    tutor_name=faker.name(),
                    student_name=faker.name(),
                    created_at=last_created_at,
                )
            else:
                group_classroom = await GroupClassroom.create(
                    **factories.GroupClassroomInputFactory.build_python(
                        subject_id=CLASSROOMS_SUBJECT_IDS[
                            i % len(CLASSROOMS_SUBJECT_IDS)
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


@classroom_requests_parametrization
async def test_student_classrooms_listing(
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


@classroom_filters_parametrization
@classroom_requests_parametrization
async def test_student_classrooms_listing_search(
    student_client: TestClient,
    student_classrooms: list[AnyClassroom],
    classroom_filters_schema: ClassroomFiltersSchema,
    offset: int,
    limit: int,
) -> None:
    filtered_student_classroom: list[AnyClassroom] = apply_filters_to_classrooms(
        classrooms=student_classrooms[offset:],
        **classroom_filters_schema.model_dump(),
    )

    assert_response(
        student_client.post(
            "/api/protected/classroom-service/roles/student/classrooms/searches/",
            json=remove_none_values(
                ClassroomSearchRequestSchema(
                    filters=classroom_filters_schema,
                    cursor=(
                        None
                        if offset == 0
                        else ClassroomCursorSchema(
                            created_at=student_classrooms[offset - 1].created_at
                        )
                    ),
                    limit=limit,
                ).model_dump(mode="json")
            ),
        ),
        expected_json=list(convert_student_classrooms(filtered_student_classroom))[
            :limit
        ],
    )
