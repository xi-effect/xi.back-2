import pytest
from pydantic_marshals.contains import UnorderedLiteralCollection
from starlette import status
from starlette.testclient import TestClient

from app.classrooms.models.classrooms_db import GroupClassroom, IndividualClassroom
from app.classrooms.models.enrollments_db import Enrollment
from tests.common.assert_contains_ext import assert_response

pytestmark = pytest.mark.anyio


async def test_listing_individual_classroom_students(
    internal_client: TestClient,
    individual_classroom: IndividualClassroom,
) -> None:
    assert_response(
        internal_client.get(
            "/internal/classroom-service"
            f"/classrooms/{individual_classroom.id}/students/",
        ),
        expected_json=[individual_classroom.student_id],
    )


async def test_listing_group_classroom_students(
    internal_client: TestClient,
    group_classroom: GroupClassroom,
    enrollment: Enrollment,
) -> None:
    assert_response(
        internal_client.get(
            f"/internal/classroom-service/classrooms/{group_classroom.id}/students/",
        ),
        expected_json=[enrollment.student_id],
    )


async def test_listing_classroom_students_classroom_not_found(
    internal_client: TestClient,
    deleted_group_classroom_id: int,
) -> None:
    assert_response(
        internal_client.get(
            "/internal/classroom-service"
            f"/classrooms/{deleted_group_classroom_id}/students/",
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Classroom not found"},
    )


# TODO maybe expand


async def test_listing_tutor_classroom_ids(
    internal_client: TestClient,
    tutor_user_id: int,
    individual_classroom: IndividualClassroom,
    group_classroom: GroupClassroom,
) -> None:
    assert_response(
        internal_client.get(
            f"/internal/classroom-service/tutors/{tutor_user_id}/classroom-ids/",
        ),
        expected_json=UnorderedLiteralCollection(
            [individual_classroom.id, group_classroom.id],
        ),
    )


async def test_listing_student_classroom_ids(
    internal_client: TestClient,
    student_user_id: int,
    individual_classroom: IndividualClassroom,
    enrollment: Enrollment,
) -> None:
    assert_response(
        internal_client.get(
            f"/internal/classroom-service/students/{student_user_id}/classroom-ids/",
        ),
        expected_json=UnorderedLiteralCollection(
            [individual_classroom.id, enrollment.group_classroom_id],
        ),
    )
