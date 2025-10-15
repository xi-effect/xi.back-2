import pytest
from freezegun import freeze_time
from pydantic_marshals.contains import assert_contains
from respx import MockRouter
from starlette import status
from starlette.testclient import TestClient

from app.classrooms.models.classrooms_db import GroupClassroom
from app.classrooms.models.enrollments_db import Enrollment
from app.classrooms.models.tutorships_db import Tutorship
from app.common.config import settings
from app.common.utils.datetime import datetime_utc_now
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.mock_stack import MockStack
from tests.common.respx_ext import assert_last_httpx_request
from tests.common.types import AnyJSON
from tests.factories import UserProfileFactory

pytestmark = pytest.mark.anyio


async def test_enrollments_listing(
    users_internal_respx_mock: MockRouter,
    tutor_client: TestClient,
    group_classroom: GroupClassroom,
    enrollment: Enrollment,
) -> None:
    student_profile: AnyJSON = UserProfileFactory.build_json()
    users_internal_bridge_mock = users_internal_respx_mock.get(
        path="/users/",
        params={"user_ids": [enrollment.student_id]},
    ).respond(json={enrollment.student_id: student_profile})

    assert_response(
        tutor_client.get(
            "/api/protected/classroom-service/roles/tutor"
            f"/group-classrooms/{group_classroom.id}/students/",
        ),
        expected_json=[student_profile],
    )

    assert_last_httpx_request(
        users_internal_bridge_mock,
        expected_headers={"X-Api-Key": settings.api_key},
    )


async def test_enrollments_listing_empty_list(
    users_internal_respx_mock: MockRouter,
    tutor_client: TestClient,
    group_classroom: GroupClassroom,
) -> None:
    assert_response(
        tutor_client.get(
            "/api/protected/classroom-service/roles/tutor"
            f"/group-classrooms/{group_classroom.id}/students/",
        ),
        expected_json=[],
    )

    users_internal_respx_mock.calls.assert_not_called()


@freeze_time()
async def test_adding_classroom_student(
    active_session: ActiveSession,
    tutor_client: TestClient,
    tutorship: Tutorship,
    group_classroom: GroupClassroom,
) -> None:
    assert_nodata_response(
        tutor_client.post(
            "/api/protected/classroom-service/roles/tutor"
            f"/group-classrooms/{group_classroom.id}/students/{tutorship.student_id}/"
        ),
        expected_code=status.HTTP_201_CREATED,
    )

    async with active_session():
        enrollment = await Enrollment.find_first_by_kwargs(
            group_classroom_id=group_classroom.id,
            student_id=tutorship.student_id,
        )
        assert enrollment is not None
        assert_contains(
            enrollment,
            {"created_at": datetime_utc_now()},
        )
        await enrollment.delete()

        assert_contains(
            await Tutorship.find_first_by_kwargs(
                tutor_id=tutorship.tutor_id, student_id=tutorship.student_id
            ),
            {"active_classroom_count": tutorship.active_classroom_count + 1},
        )

        assert_contains(
            await GroupClassroom.find_first_by_id(group_classroom.id),
            {"enrollments_count": group_classroom.enrollments_count + 1},
        )


async def test_adding_classroom_student_enrollment_already_exists(
    tutor_client: TestClient,
    group_classroom: GroupClassroom,
    enrollment: Enrollment,
) -> None:
    assert_response(
        tutor_client.post(
            "/api/protected/classroom-service/roles/tutor"
            f"/group-classrooms/{group_classroom.id}/students/{enrollment.student_id}/"
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={"detail": "Enrollment already exists"},
    )


async def test_adding_classroom_student_quantity_exceeded(
    mock_stack: MockStack,
    tutor_client: TestClient,
    tutorship: Tutorship,
    group_classroom: GroupClassroom,
) -> None:
    mock_stack.enter_mock(
        GroupClassroom, "max_enrollments_count_per_group", property_value=0
    )

    assert_response(
        tutor_client.post(
            "/api/protected/classroom-service/roles/tutor"
            f"/group-classrooms/{group_classroom.id}/students/{tutorship.student_id}/"
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={"detail": "Quantity exceeded"},
    )


async def test_adding_classroom_student_tutorship_not_found(
    student_user_id: int,
    tutor_client: TestClient,
    group_classroom: GroupClassroom,
) -> None:
    assert_response(
        tutor_client.post(
            "/api/protected/classroom-service/roles/tutor"
            f"/group-classrooms/{group_classroom.id}/students/{student_user_id}/"
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Tutorship not found"},
    )


async def test_removing_classroom_student(
    active_session: ActiveSession,
    tutor_client: TestClient,
    group_classroom: GroupClassroom,
    tutorship: Tutorship,
    enrollment: Enrollment,
) -> None:
    assert_nodata_response(
        tutor_client.delete(
            "/api/protected/classroom-service/roles/tutor"
            f"/group-classrooms/{enrollment.group_classroom_id}/students/{enrollment.student_id}/"
        ),
    )

    async with active_session():
        assert (
            await Enrollment.find_first_by_kwargs(
                group_classroom_id=enrollment.group_classroom_id,
                student_id=enrollment.student_id,
            )
            is None
        )

        assert_contains(
            await Tutorship.find_first_by_kwargs(
                tutor_id=tutorship.tutor_id, student_id=tutorship.student_id
            ),
            {"active_classroom_count": tutorship.active_classroom_count - 1},
        )

        assert_contains(
            await GroupClassroom.find_first_by_id(group_classroom.id),
            {"enrollments_count": group_classroom.enrollments_count - 1},
        )


async def test_removing_classroom_student_enrollment_not_found(
    tutor_client: TestClient,
    tutorship: Tutorship,
    group_classroom: GroupClassroom,
) -> None:
    assert_response(
        tutor_client.delete(
            "/api/protected/classroom-service/roles/tutor"
            f"/group-classrooms/{group_classroom.id}/students/{tutorship.student_id}/"
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Enrollment not found"},
    )


@pytest.mark.parametrize(
    "method",
    [
        pytest.param("POST", id="add"),
        pytest.param("DELETE", id="remove"),
    ],
)
async def test_adding_classroom_student_classroom_not_found(
    tutor_client: TestClient,
    tutorship: Tutorship,
    deleted_group_classroom_id: int,
    method: str,
) -> None:
    assert_response(
        tutor_client.request(
            method=method,
            url=(
                "/api/protected/classroom-service/roles/tutor"
                f"/group-classrooms/{deleted_group_classroom_id}/students/{tutorship.student_id}/"
            ),
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Classroom not found"},
    )
