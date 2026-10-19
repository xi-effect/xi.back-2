from collections.abc import Iterator
from typing import assert_never

import pytest
from starlette.testclient import TestClient

from app.classrooms.models.classrooms_db import (
    AnyClassroom,
    ClassroomStatus,
    GroupClassroom,
    IndividualClassroom,
)
from tests.classrooms.conftest import (
    CLASSROOM_STATUSES,
    CLASSROOMS_LIST_SIZE,
    CLASSROOMS_PER_STATUS,
)
from tests.common.assert_contains_ext import assert_response
from tests.common.types import AnyJSON
from tests.common.utils import remove_none_values

pytestmark = pytest.mark.anyio


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


@pytest.mark.parametrize(
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
async def test_tutor_classrooms_listing(
    tutor_client: TestClient,
    tutor_classrooms: list[AnyClassroom],
    offset: int | None,
    limit: int,
) -> None:
    cursor = None if offset is None else tutor_classrooms[offset]

    assert_response(
        tutor_client.post(
            "/api/protected/classroom-service/roles/tutor/classrooms/searches/",
            json={
                "cursor": (
                    None
                    if cursor is None
                    else {"created_at": cursor.created_at.isoformat()}
                ),
                "limit": limit,
                "filters": {},
            },
        ),
        expected_json=list(
            convert_tutor_classrooms(
                tutor_classrooms=[
                    classroom
                    for classroom in tutor_classrooms
                    if cursor is None or classroom.created_at < cursor.created_at
                ]
            )
        )[:limit],
    )


@pytest.mark.parametrize(
    "statuses",
    [
        *[pytest.param({status}, id=status) for status in CLASSROOM_STATUSES],
        pytest.param(set(CLASSROOM_STATUSES), id="all_statuses"),
    ],
)
async def test_tutor_classrooms_listing_filtered_by_statuses(
    tutor_client: TestClient,
    tutor_classrooms: list[AnyClassroom],
    statuses: set[ClassroomStatus],
) -> None:
    assert_response(
        tutor_client.post(
            "/api/protected/classroom-service/roles/tutor/classrooms/searches/",
            json={
                "limit": CLASSROOMS_LIST_SIZE,
                "filters": {"statuses": list(statuses)},
            },
        ),
        expected_json=list(
            convert_tutor_classrooms(
                tutor_classrooms=[
                    classroom
                    for classroom in tutor_classrooms
                    if classroom.status in statuses
                ]
            )
        ),
    )


async def test_tutor_classroom_status_counts_retrieving(
    tutor_client: TestClient,
    tutor_classrooms: list[AnyClassroom],
) -> None:
    assert_response(
        tutor_client.get(
            "/api/protected/classroom-service/roles/tutor/classroom-status-counts/",
        ),
        expected_json={
            "active": CLASSROOMS_PER_STATUS,
            "paused": CLASSROOMS_PER_STATUS,
            "locked": CLASSROOMS_PER_STATUS,
            "finished": CLASSROOMS_PER_STATUS,
        },
    )


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
