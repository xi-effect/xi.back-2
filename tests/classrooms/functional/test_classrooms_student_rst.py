import pytest
from starlette import status
from starlette.testclient import TestClient

from app.classrooms.models.classrooms_db import (
    AnyClassroom,
    Classroom,
)
from app.classrooms.models.enrollments_db import Enrollment
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.types import AnyJSON

pytestmark = pytest.mark.anyio


async def test_individual_classroom_retrieving(
    student_client: TestClient,
    individual_classroom: AnyClassroom,
    individual_classroom_student_data: AnyJSON,
) -> None:
    assert_response(
        student_client.get(
            f"/api/protected/classroom-service/roles/student/classrooms/{individual_classroom.id}/",
        ),
        expected_json=individual_classroom_student_data,
    )


async def test_group_classroom_retrieving(
    student_client: TestClient,
    group_classroom_student_data: AnyJSON,
    enrollment: Enrollment,
) -> None:
    assert_response(
        student_client.get(
            f"/api/protected/classroom-service/roles/student/classrooms/{enrollment.group_classroom_id}/",
        ),
        expected_json=group_classroom_student_data,
    )


async def test_classroom_access_verification(
    student_client: TestClient,
    group_classroom_student_data: AnyJSON,
    enrollment: Enrollment,
) -> None:
    assert_nodata_response(
        student_client.get(
            f"/api/protected/classroom-service/roles/student/classrooms/{enrollment.group_classroom_id}/access/",
        ),
    )


student_classroom_request_parametrization = pytest.mark.parametrize(
    "path",
    [
        pytest.param(
            "",
            id="retrieve_classroom",
        ),
        pytest.param(
            "access/",
            id="verify_classroom_access",
        ),
    ],
)


@student_classroom_request_parametrization
async def test_classroom_requesting_access_denied(
    outsider_client: TestClient,
    any_classroom: AnyClassroom,
    path: str,
) -> None:
    assert_response(
        outsider_client.get(
            f"/api/protected/classroom-service/roles/student/classrooms/{any_classroom.id}/{path}"
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_json={"detail": "Classroom student access denied"},
    )


@student_classroom_request_parametrization
async def test_individual_classroom_not_finding(
    active_session: ActiveSession,
    student_client: TestClient,
    individual_classroom: AnyClassroom,
    path: str,
) -> None:
    async with active_session():
        await Classroom.delete_by_kwargs(id=individual_classroom.id)

    assert_response(
        student_client.get(
            f"/api/protected/classroom-service/roles/student/classrooms/{individual_classroom.id}/{path}"
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Classroom not found"},
    )


@student_classroom_request_parametrization
async def test_group_classroom_not_finding(
    active_session: ActiveSession,
    student_client: TestClient,
    enrollment: Enrollment,
    path: str,
) -> None:
    async with active_session():
        await Classroom.delete_by_kwargs(id=enrollment.group_classroom_id)

    assert_response(
        student_client.get(
            f"/api/protected/classroom-service/roles/student/classrooms/{enrollment.group_classroom_id}/{path}"
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Classroom not found"},
    )
