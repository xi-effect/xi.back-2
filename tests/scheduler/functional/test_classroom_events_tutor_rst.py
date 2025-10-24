from typing import Any

import pytest
from starlette import status
from starlette.testclient import TestClient

from app.scheduler.models.events_db import ClassroomEvent, EventKind
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.polyfactory_ext import BaseModelFactory
from tests.common.types import AnyJSON
from tests.scheduler.factories import (
    ClassroomEventInputFactory,
    ClassroomEventInvalidTimeFrameInputFactory,
)

pytestmark = pytest.mark.anyio


async def test_tutor_classroom_event_creation(
    active_session: ActiveSession,
    tutor_client: TestClient,
    classroom_id: int,
) -> None:
    classroom_event_input_data = ClassroomEventInputFactory.build_json()

    classroom_event_id: int = assert_response(
        tutor_client.post(
            f"/api/protected/scheduler-service/roles/tutor/classrooms/{classroom_id}/events/",
            json=classroom_event_input_data,
        ),
        expected_code=status.HTTP_201_CREATED,
        expected_json={
            **classroom_event_input_data,
            "id": int,
            "classroom_id": classroom_id,
            "kind": EventKind.CLASSROOM,
        },
    ).json()["id"]

    async with active_session():
        classroom_event = await ClassroomEvent.find_first_by_id(classroom_event_id)
        assert classroom_event is not None
        await classroom_event.delete()


async def test_tutor_classroom_event_creation_invalid_time_frame(
    tutor_client: TestClient,
    classroom_id: int,
) -> None:
    assert_response(
        tutor_client.post(
            f"/api/protected/scheduler-service/roles/tutor/classrooms/{classroom_id}/events/",
            json=ClassroomEventInvalidTimeFrameInputFactory.build_json(),
        ),
        expected_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        expected_json={
            "detail": [
                {
                    "type": "value_error",
                    "loc": ["body"],
                    "msg": "Value error, the start time of an event cannot be greater than or equal to the end time",
                }
            ]
        },
    )


async def test_tutor_classroom_event_retrieving(
    tutor_client: TestClient,
    classroom_event: ClassroomEvent,
    classroom_event_data: AnyJSON,
) -> None:
    assert_response(
        tutor_client.get(
            "/api/protected/scheduler-service/roles/tutor"
            f"/classrooms/{classroom_event.classroom_id}/events/{classroom_event.id}/",
        ),
        expected_json=classroom_event_data,
    )


async def test_tutor_classroom_event_updating(
    tutor_client: TestClient,
    classroom_event: ClassroomEvent,
    classroom_event_data: AnyJSON,
) -> None:
    classroom_event_put_data = ClassroomEventInputFactory.build_json()

    assert_response(
        tutor_client.put(
            "/api/protected/scheduler-service/roles/tutor"
            f"/classrooms/{classroom_event.classroom_id}/events/{classroom_event.id}/",
            json=classroom_event_put_data,
        ),
        expected_json={**classroom_event_data, **classroom_event_put_data},
    )


async def test_tutor_classroom_event_updating_invalid_time_frame(
    tutor_client: TestClient,
    classroom_event: ClassroomEvent,
) -> None:
    assert_response(
        tutor_client.put(
            "/api/protected/scheduler-service/roles/tutor"
            f"/classrooms/{classroom_event.classroom_id}/events/{classroom_event.id}/",
            json=ClassroomEventInvalidTimeFrameInputFactory.build_json(),
        ),
        expected_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        expected_json={
            "detail": [
                {
                    "type": "value_error",
                    "loc": ["body"],
                    "msg": "Value error, the start time of an event cannot be greater than or equal to the end time",
                }
            ]
        },
    )


async def test_tutor_classroom_event_deleting(
    active_session: ActiveSession,
    tutor_client: TestClient,
    classroom_event: ClassroomEvent,
) -> None:
    assert_nodata_response(
        tutor_client.delete(
            "/api/protected/scheduler-service/roles/tutor"
            f"/classrooms/{classroom_event.classroom_id}/events/{classroom_event.id}/",
        )
    )

    async with active_session():
        assert await ClassroomEvent.find_first_by_id(classroom_event.id) is None


tutor_classroom_events_request_parametrization = pytest.mark.parametrize(
    ("method", "body_factory"),
    [
        pytest.param("GET", None, id="retrieve"),
        pytest.param("PUT", ClassroomEventInputFactory, id="update"),
        pytest.param("DELETE", None, id="delete"),
    ],
)


@tutor_classroom_events_request_parametrization
async def test_tutor_classroom_event_requesting_access_denied(
    tutor_client: TestClient,
    other_classroom_id: int,
    classroom_event: ClassroomEvent,
    method: str,
    body_factory: type[BaseModelFactory[Any]] | None,
) -> None:
    assert_response(
        tutor_client.request(
            method=method,
            url="/api/protected/scheduler-service/roles/tutor"
            f"/classrooms/{other_classroom_id}/events/{classroom_event.id}/",
            json=body_factory and body_factory.build_json(),
        ),
        expected_code=status.HTTP_403_FORBIDDEN,
        expected_json={"detail": "Classroom event access denied"},
    )


@tutor_classroom_events_request_parametrization
async def test_tutor_classroom_event_requesting_not_finding(
    tutor_client: TestClient,
    classroom_id: int,
    deleted_classroom_event_id: int,
    method: str,
    body_factory: type[BaseModelFactory[Any]] | None,
) -> None:
    assert_response(
        tutor_client.request(
            method=method,
            url="/api/protected/scheduler-service/roles/tutor"
            f"/classrooms/{classroom_id}/events/{deleted_classroom_event_id}/",
            json=body_factory and body_factory.build_json(),
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Classroom event not found"},
    )
