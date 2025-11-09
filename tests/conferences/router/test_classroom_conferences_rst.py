import random
from unittest.mock import AsyncMock

import pytest
from faker import Faker
from livekit.protocol.models import Room
from respx import MockRouter
from starlette import status
from starlette.testclient import TestClient

from app.common.config import settings
from app.common.schemas.notifications_sch import (
    ClassroomNotificationPayloadSchema,
    NotificationInputSchema,
    NotificationKind,
)
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.mock_stack import MockStack
from tests.common.respx_ext import assert_last_httpx_request
from tests.conferences.conftest import ClassroomRoleType
from tests.conferences.factories import ConferenceParticipantFactory

pytestmark = pytest.mark.anyio


async def test_classroom_conference_reactivation(
    mock_stack: MockStack,
    classrooms_respx_mock: MockRouter,
    send_notification_mock: AsyncMock,
    outsider_client: TestClient,
    classroom_id: int,
    classroom_conference_room_name: str,
) -> None:
    conferences_svc_mock = mock_stack.enter_async_mock(
        "app.conferences.services.conferences_svc.reactivate_room"
    )

    recipient_user_ids = random.choices(list(range(100)), k=random.randint(2, 10))
    classroom_bridge_mock = classrooms_respx_mock.get(
        path=f"/classrooms/{classroom_id}/students/"
    ).respond(json=recipient_user_ids)

    assert_nodata_response(
        outsider_client.post(
            "/api/protected/conference-service/roles/tutor"
            f"/classrooms/{classroom_id}/conference/",
        ),
    )

    send_notification_mock.assert_awaited_once_with(
        NotificationInputSchema(
            payload=ClassroomNotificationPayloadSchema(
                kind=NotificationKind.CLASSROOM_CONFERENCE_STARTED_V1,
                classroom_id=classroom_id,
            ),
            recipient_user_ids=recipient_user_ids,
        )
    )

    assert_last_httpx_request(
        classroom_bridge_mock,
        expected_headers={"X-Api-Key": settings.api_key},
    )

    conferences_svc_mock.assert_awaited_once_with(
        livekit_room_name=classroom_conference_room_name
    )


async def test_classroom_conference_access_token_generation(
    faker: Faker,
    mock_stack: MockStack,
    outsider_client: TestClient,
    outsider_user_id: int,
    parametrized_classroom_role: ClassroomRoleType,
    classroom_id: int,
    classroom_conference_room_name: str,
    classroom_conference_room: Room,
) -> None:
    access_token = faker.pystr()

    find_room_by_name_mock = mock_stack.enter_async_mock(
        "app.conferences.services.conferences_svc.find_room_by_name",
        return_value=classroom_conference_room,
    )
    generate_access_token_mock = mock_stack.enter_async_mock(
        "app.conferences.services.conferences_svc.generate_access_token",
        return_value=access_token,
    )

    assert_response(
        outsider_client.post(
            f"/api/protected/conference-service/roles/{parametrized_classroom_role}"
            f"/classrooms/{classroom_id}/conference/access-tokens/",
        ),
        expected_json=access_token,
    )

    find_room_by_name_mock.assert_awaited_once_with(
        livekit_room_name=classroom_conference_room_name
    )
    generate_access_token_mock.assert_awaited_once_with(
        livekit_room=classroom_conference_room, user_id=outsider_user_id
    )


async def test_classroom_conference_participants_listing(
    faker: Faker,
    mock_stack: MockStack,
    outsider_client: TestClient,
    outsider_user_id: int,
    parametrized_classroom_role: ClassroomRoleType,
    classroom_id: int,
    classroom_conference_room_name: str,
    classroom_conference_room: Room,
) -> None:
    participants = ConferenceParticipantFactory.batch(faker.random_int(2, 5))

    find_room_by_name_mock = mock_stack.enter_async_mock(
        "app.conferences.services.conferences_svc.find_room_by_name",
        return_value=classroom_conference_room,
    )
    list_room_participants_mock = mock_stack.enter_async_mock(
        "app.conferences.services.conferences_svc.list_room_participants",
        return_value=participants,
    )

    assert_response(
        outsider_client.get(
            f"/api/protected/conference-service/roles/{parametrized_classroom_role}"
            f"/classrooms/{classroom_id}/conference/participants/",
        ),
        expected_json=[
            participant.model_dump(mode="json") for participant in participants
        ],
    )

    find_room_by_name_mock.assert_awaited_once_with(
        livekit_room_name=classroom_conference_room_name
    )
    list_room_participants_mock.assert_awaited_once_with(
        livekit_room_name=classroom_conference_room_name,
    )


@pytest.mark.parametrize(
    ("method", "path"),
    [
        pytest.param("POST", "access-tokens/", id="generate_access_token"),
        pytest.param("GET", "participants/", id="list_participants"),
    ],
)
async def test_classroom_conference_requesting_conference_not_active(
    mock_stack: MockStack,
    outsider_client: TestClient,
    parametrized_classroom_role: str,
    classroom_id: int,
    classroom_conference_room_name: str,
    method: str,
    path: str,
) -> None:
    find_room_by_name_mock = mock_stack.enter_async_mock(
        "app.conferences.services.conferences_svc.find_room_by_name",
    )

    assert_response(
        outsider_client.request(
            method=method,
            url=(
                f"/api/protected/conference-service/roles/{parametrized_classroom_role}"
                f"/classrooms/{classroom_id}/conference/{path}"
            ),
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={"detail": "Conference is not active"},
    )

    find_room_by_name_mock.assert_awaited_once_with(
        livekit_room_name=classroom_conference_room_name
    )
