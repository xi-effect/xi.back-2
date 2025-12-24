import pytest
from starlette import status
from starlette.testclient import TestClient

from app.scheduler.models.events_db import ClassroomEvent
from tests.common.assert_contains_ext import assert_response
from tests.common.types import AnyJSON

pytestmark = pytest.mark.anyio


async def test_student_classroom_events_retrieving(
    student_client: TestClient,
    classroom_event: ClassroomEvent,
    classroom_event_data: AnyJSON,
) -> None:
    assert_response(
        student_client.get(
            "/api/protected/scheduler-service/roles/student"
            f"/classrooms/{classroom_event.classroom_id}/events/{classroom_event.id}/",
        ),
        expected_json=classroom_event_data,
    )


async def test_student_classroom_event_requesting_access_denied(
    student_client: TestClient,
    other_classroom_id: int,
    classroom_event: ClassroomEvent,
) -> None:
    assert_response(
        student_client.get(
            "/api/protected/scheduler-service/roles/student"
            f"/classrooms/{other_classroom_id}/events/{classroom_event.id}/",
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_json={"detail": "Classroom event access denied"},
    )


async def test_student_classroom_event_requesting_not_finding(
    student_client: TestClient,
    classroom_id: int,
    deleted_classroom_event_id: int,
) -> None:
    assert_response(
        student_client.get(
            "/api/protected/scheduler-service/roles/student"
            f"/classrooms/{classroom_id}/events/{deleted_classroom_event_id}/",
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Classroom event not found"},
    )
