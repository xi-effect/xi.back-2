import pytest
from pydantic_marshals.contains import UnorderedLiteralCollection
from starlette.testclient import TestClient

from app.classrooms.models.classrooms_db import AnyClassroom, ClassroomStatus
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_response

pytestmark = pytest.mark.anyio

NON_ACTIVE_STATUSES = [
    ClassroomStatus.PAUSED,
    ClassroomStatus.LOCKED,
    ClassroomStatus.FINISHED,
]

active_only_parametrization = pytest.mark.parametrize(
    "active_only",
    [
        pytest.param(False, id="all"),
        pytest.param(True, id="active_only"),
    ],
)


async def mark_some_classrooms_non_active(
    active_session: ActiveSession,
    classrooms: list[AnyClassroom],
) -> None:
    non_active_classrooms = [
        classroom for i, classroom in enumerate(classrooms) if i % 3 != 0
    ]
    async with active_session() as session:
        for i, classroom in enumerate(non_active_classrooms):
            session.add(classroom)
            classroom.status = NON_ACTIVE_STATUSES[i % len(NON_ACTIVE_STATUSES)]


def expected_active_only_classroom_ids(
    classrooms: list[AnyClassroom],
    active_only: bool,
) -> list[int]:
    return [
        classroom.id
        for classroom in classrooms
        if not active_only or classroom.status is ClassroomStatus.ACTIVE
    ]


@active_only_parametrization
async def test_tutor_classroom_ids_filtered_by_active_status(
    active_session: ActiveSession,
    internal_client: TestClient,
    tutor_user_id: int,
    tutor_classrooms: list[AnyClassroom],
    active_only: bool,
) -> None:
    await mark_some_classrooms_non_active(active_session, tutor_classrooms)

    assert_response(
        internal_client.get(
            f"/internal/classroom-service/tutors/{tutor_user_id}/classroom-ids/",
            params={"active_only": active_only},
        ),
        expected_json=UnorderedLiteralCollection(
            expected_active_only_classroom_ids(tutor_classrooms, active_only)
        ),
    )


@active_only_parametrization
async def test_student_classroom_ids_filtered_by_active_status(
    active_session: ActiveSession,
    internal_client: TestClient,
    student_user_id: int,
    student_classrooms: list[AnyClassroom],
    active_only: bool,
) -> None:
    await mark_some_classrooms_non_active(active_session, student_classrooms)

    assert_response(
        internal_client.get(
            f"/internal/classroom-service/students/{student_user_id}/classroom-ids/",
            params={"active_only": active_only},
        ),
        expected_json=UnorderedLiteralCollection(
            expected_active_only_classroom_ids(student_classrooms, active_only)
        ),
    )
