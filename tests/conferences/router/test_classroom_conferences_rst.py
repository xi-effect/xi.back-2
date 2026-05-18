from unittest.mock import AsyncMock

import pytest
from faker import Faker
from livekit.protocol.models import ParticipantInfo, Room
from pytest_lazy_fixtures import lf, lfc
from starlette import status
from starlette.testclient import TestClient

from app.common.schemas.classrooms_sch import ClassroomRole
from app.common.schemas.notifications_sch import (
    ClassroomNotificationPayloadSchema,
    ClassroomParticipantRecipientFilterSchema,
    NotificationInputV2Schema,
    NotificationKind,
)
from app.conferences.schemas.conferences_sch import (
    ParticipantMetadataSchema,
    RoomMetadataSchema,
)
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.mock_stack import MockStack
from tests.conferences.conftest import ClassroomRoleType
from tests.conferences.factories import (
    ConferenceParticipantFactory,
    ParticipantMetadataFactory,
    RoomMetadataFactory,
)

pytestmark = pytest.mark.anyio


async def test_classroom_conference_reactivation(
    mock_stack: MockStack,
    send_notification_mock: AsyncMock,
    outsider_client: TestClient,
    classroom_id: int,
    classroom_conference_room_name: str,
) -> None:
    conferences_svc_mock = mock_stack.enter_async_mock(
        "app.conferences.services.conferences_svc.reactivate_room"
    )

    assert_nodata_response(
        outsider_client.post(
            "/api/protected/conference-service/roles/tutor"
            f"/classrooms/{classroom_id}/conference/",
        ),
    )

    send_notification_mock.assert_awaited_once_with(
        NotificationInputV2Schema(
            payload=ClassroomNotificationPayloadSchema(
                kind=NotificationKind.CLASSROOM_CONFERENCE_STARTED_V1,
                classroom_id=classroom_id,
            ),
            recipient_filters=[
                ClassroomParticipantRecipientFilterSchema(
                    classroom_id=classroom_id,
                    role=ClassroomRole.STUDENT,
                )
            ],
        )
    )

    conferences_svc_mock.assert_awaited_once_with(
        livekit_room_name=classroom_conference_room_name
    )


async def test_classroom_conference_metadata_updating(
    mock_stack: MockStack,
    outsider_client: TestClient,
    classroom_id: int,
    classroom_conference_room_name: str,
    classroom_conference_room: Room,
) -> None:
    new_room_metadata: RoomMetadataSchema = RoomMetadataFactory.build()

    find_room_by_name_mock = mock_stack.enter_async_mock(
        "app.conferences.services.conferences_svc.find_room_by_name",
        return_value=classroom_conference_room,
    )
    update_room_metadata_mock = mock_stack.enter_async_mock(
        "app.conferences.services.conferences_svc.update_room_metadata"
    )

    assert_nodata_response(
        outsider_client.put(
            "/api/protected/conference-service/roles/tutor"
            f"/classrooms/{classroom_id}/conference/metadata/",
            json=new_room_metadata.model_dump(),
        ),
    )

    find_room_by_name_mock.assert_awaited_once_with(
        livekit_room_name=classroom_conference_room_name,
    )
    update_room_metadata_mock.assert_awaited_once_with(
        livekit_room=classroom_conference_room,
        metadata=new_room_metadata,
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
        livekit_room=classroom_conference_room,
        user_id=outsider_user_id,
    )


async def test_classroom_conference_participants_listing(
    faker: Faker,
    mock_stack: MockStack,
    outsider_client: TestClient,
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


participant_metadata_updating_request_parametrization = pytest.mark.parametrize(
    ("participant_user_id", "participant_user_id_in_path", "role"),
    [
        pytest.param(
            lf("outsider_user_id"),
            "current",
            "tutor",
            id="tutor-current_participant",
        ),
        pytest.param(
            lf("outsider_user_id"),
            "current",
            "student",
            id="student-current_participant",
        ),
        pytest.param(
            lf("other_user_id"),
            lf("other_user_id"),
            "tutor",
            id="tutor-current_participant",
        ),
    ],
)


@participant_metadata_updating_request_parametrization
async def test_classroom_conference_participant_metadata_updating(
    faker: Faker,
    mock_stack: MockStack,
    outsider_client: TestClient,
    outsider_user_id: int,
    classroom_id: int,
    classroom_conference_room_name: str,
    classroom_conference_room: Room,
    role: ClassroomRoleType,
    participant_user_id: int,
    participant_user_id_in_path: int | str,
) -> None:
    new_participant_metadata: ParticipantMetadataSchema = (
        ParticipantMetadataFactory.build()
    )
    new_participant_info = ParticipantInfo(
        name=faker.user_name(),
        identity=str(participant_user_id),
        metadata=new_participant_metadata.model_dump_metadata_json(),
    )

    find_room_by_name_mock = mock_stack.enter_async_mock(
        "app.conferences.services.conferences_svc.find_room_by_name",
        return_value=classroom_conference_room,
    )
    update_participant_metadata_mock = mock_stack.enter_async_mock(
        "app.conferences.services.conferences_svc.update_participant_metadata",
        return_value=new_participant_info,
    )

    assert_nodata_response(
        outsider_client.put(
            f"/api/protected/conference-service/roles/{role}"
            f"/classrooms/{classroom_id}/conference"
            f"/participants/{participant_user_id_in_path}/metadata/",
            json=new_participant_metadata.model_dump(),
        ),
    )

    find_room_by_name_mock.assert_awaited_once_with(
        livekit_room_name=classroom_conference_room_name
    )
    update_participant_metadata_mock.assert_awaited_once_with(
        livekit_room=classroom_conference_room,
        user_id=participant_user_id,
        metadata=new_participant_metadata,
    )


@participant_metadata_updating_request_parametrization
async def test_classroom_conference_participant_metadata_updating_participant_not_found(
    faker: Faker,
    mock_stack: MockStack,
    outsider_client: TestClient,
    outsider_user_id: int,
    classroom_id: int,
    classroom_conference_room_name: str,
    classroom_conference_room: Room,
    role: ClassroomRoleType,
    participant_user_id: int,
    participant_user_id_in_path: int | str,
) -> None:
    new_participant_metadata: ParticipantMetadataSchema = (
        ParticipantMetadataFactory.build()
    )

    find_room_by_name_mock = mock_stack.enter_async_mock(
        "app.conferences.services.conferences_svc.find_room_by_name",
        return_value=classroom_conference_room,
    )
    update_participant_metadata_mock = mock_stack.enter_async_mock(
        "app.conferences.services.conferences_svc.update_participant_metadata",
    )

    assert_response(
        outsider_client.put(
            f"/api/protected/conference-service/roles/{role}"
            f"/classrooms/{classroom_id}/conference"
            f"/participants/{participant_user_id_in_path}/metadata/",
            json=new_participant_metadata.model_dump(),
        ),
        expected_code=status.HTTP_404_NOT_FOUND,
        expected_json={"detail": "Conference participant not found"},
    )

    find_room_by_name_mock.assert_awaited_once_with(
        livekit_room_name=classroom_conference_room_name
    )
    update_participant_metadata_mock.assert_awaited_once_with(
        livekit_room=classroom_conference_room,
        user_id=participant_user_id,
        metadata=new_participant_metadata,
    )


@pytest.mark.parametrize(
    ("method", "path", "role"),
    [
        pytest.param("PUT", "metadata/", "tutor", id="update_room_metadata-tutor"),
        pytest.param(
            "POST",
            "access-tokens/",
            "tutor",
            id="generate_access_token-tutor",
        ),
        pytest.param(
            "POST",
            "access-tokens/",
            "student",
            id="generate_access_token-student",
        ),
        pytest.param("GET", "participants/", "tutor", id="list_participants-tutor"),
        pytest.param("GET", "participants/", "student", id="list_participants-student"),
        pytest.param(
            "PUT",
            "participants/current/metadata/",
            "tutor",
            id="update_current_participant_metadata-tutor",
        ),
        pytest.param(
            "PUT",
            "participants/current/metadata/",
            "student",
            id="update_current_participant_metadata-student",
        ),
        pytest.param(
            "PUT",
            lfc(lambda other_user_id: f"participants/{other_user_id}/metadata/"),
            "tutor",
            id="update_other_participant_metadata-tutor",
        ),
    ],
)
async def test_classroom_conference_requesting_conference_not_active(
    mock_stack: MockStack,
    outsider_client: TestClient,
    classroom_id: int,
    classroom_conference_room_name: str,
    method: str,
    path: str,
    role: ClassroomRoleType,
) -> None:
    find_room_by_name_mock = mock_stack.enter_async_mock(
        "app.conferences.services.conferences_svc.find_room_by_name",
    )

    assert_response(
        outsider_client.request(
            method=method,
            url=(
                f"/api/protected/conference-service/roles/{role}"
                f"/classrooms/{classroom_id}/conference/{path}"
            ),
        ),
        expected_code=status.HTTP_409_CONFLICT,
        expected_json={"detail": "Conference is not active"},
    )

    find_room_by_name_mock.assert_awaited_once_with(
        livekit_room_name=classroom_conference_room_name
    )
