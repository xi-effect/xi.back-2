import pytest
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
