from collections.abc import Iterator
from typing import assert_never

import pytest
from starlette.testclient import TestClient

from app.classrooms.models.classrooms_db import (
    AnyClassroom,
    GroupClassroom,
    IndividualClassroom,
)
from tests.classrooms.conftest import CLASSROOMS_LIST_SIZE
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
