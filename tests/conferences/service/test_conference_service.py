import jwt
import pytest
from faker import Faker
from livekit.api import TwirpError, TwirpErrorCode
from livekit.protocol.models import ParticipantInfo, Room
from livekit.protocol.room import (
    CreateRoomRequest,
    ListParticipantsRequest,
    ListParticipantsResponse,
    ListRoomsRequest,
    ListRoomsResponse,
    UpdateParticipantRequest,
    UpdateRoomMetadataRequest,
)
from pydantic_marshals.contains import assert_contains
from respx import MockRouter
from starlette import status

from app.common.config import settings
from app.conferences.schemas.conferences_sch import (
    ConferenceParticipantSchema,
    ParticipantMetadataSchema,
    RoomMetadataSchema,
)
from app.conferences.services import conferences_svc
from tests.common.livekit_testing import LiveKitMock
from tests.common.respx_ext import assert_last_httpx_request
from tests.common.types import AnyJSON
from tests.conferences.factories import (
    ConferenceParticipantFactory,
    ParticipantMetadataFactory,
    RoomMetadataFactory,
)
from tests.factories import UserProfileFactory

pytestmark = pytest.mark.anyio


@pytest.fixture()
def livekit_room_name(faker: Faker) -> str:
    return faker.user_name()


@pytest.fixture()
def default_livekit_room(livekit_room_name: str) -> Room:
    return Room(
        name=livekit_room_name,
        metadata=RoomMetadataSchema().model_dump_metadata_json(),
    )


async def test_room_reactivation(
    livekit_mock: LiveKitMock,
    livekit_room_name: str,
    default_livekit_room: Room,
) -> None:
    create_room_mock = livekit_mock.route(
        "RoomService", "CreateRoom", default_livekit_room
    )

    result = await conferences_svc.reactivate_room(livekit_room_name=livekit_room_name)
    assert result == default_livekit_room

    create_room_mock.assert_requested_once_with(
        CreateRoomRequest(
            name=livekit_room_name,
            metadata=RoomMetadataSchema().model_dump_metadata_json(),
        )
    )


@pytest.mark.parametrize(
    "is_room_found",
    [
        pytest.param(True, id="room_exists"),
        pytest.param(False, id="room_not_found"),
    ],
)
async def test_room_finding_by_name(
    livekit_mock: LiveKitMock,
    default_livekit_room: Room,
    is_room_found: bool,
) -> None:
    list_rooms_mock = livekit_mock.route(
        "RoomService",
        "ListRooms",
        ListRoomsResponse(rooms=[default_livekit_room] if is_room_found else []),
    )

    result = await conferences_svc.find_room_by_name(
        livekit_room_name=default_livekit_room.name
    )
    if is_room_found:
        assert result == default_livekit_room
    else:
        assert result is None

    list_rooms_mock.assert_requested_once_with(
        ListRoomsRequest(names=[default_livekit_room.name])
    )


async def test_room_updating(
    livekit_mock: LiveKitMock,
    default_livekit_room: Room,
) -> None:
    new_room_metadata: RoomMetadataSchema = RoomMetadataFactory.build()
    updated_livekit_room = Room(
        name=default_livekit_room.name,
        metadata=new_room_metadata.model_dump_metadata_json(),
    )

    create_room_mock = livekit_mock.route(
        "RoomService", "UpdateRoomMetadata", updated_livekit_room
    )

    result = await conferences_svc.update_room_metadata(
        livekit_room=default_livekit_room,
        metadata=new_room_metadata,
    )
    assert result == updated_livekit_room

    create_room_mock.assert_requested_once_with(
        UpdateRoomMetadataRequest(
            room=default_livekit_room.name,
            metadata=new_room_metadata.model_dump_metadata_json(),
        )
    )


async def test_conference_access_token_generation(
    faker: Faker,
    users_internal_respx_mock: MockRouter,
    default_livekit_room: Room,
) -> None:
    user_id: int = faker.random_int()
    user_profile_data: AnyJSON = UserProfileFactory.build_json()
    users_internal_bridge_mock = users_internal_respx_mock.get(
        path=f"/users/{user_id}/"
    ).respond(json=user_profile_data)

    access_token = await conferences_svc.generate_access_token(
        livekit_room=default_livekit_room,
        user_id=user_id,
    )

    assert_contains(
        jwt.decode(access_token, settings.livekit_api_secret, algorithms=["HS256"]),
        {
            "sub": str(user_id),
            "name": user_profile_data["display_name"],
            "video": {"room": default_livekit_room.name},
        },
    )

    assert_last_httpx_request(
        users_internal_bridge_mock,
        expected_headers={"X-Api-Key": settings.api_key},
    )


async def test_listing_room_participants(
    faker: Faker,
    livekit_mock: LiveKitMock,
    livekit_room_name: str,
) -> None:
    participants: list[ConferenceParticipantSchema] = (
        ConferenceParticipantFactory.batch(faker.random_int(2, 5))
    )

    list_participants_mock = livekit_mock.route(
        "RoomService",
        "ListParticipants",
        ListParticipantsResponse(
            participants=[
                ParticipantInfo(
                    name=participant.display_name,
                    identity=str(participant.user_id),
                    metadata=ParticipantMetadataSchema().model_dump_metadata_json(),
                )
                for participant in participants
            ]
        ),
    )

    assert_contains(
        await conferences_svc.list_room_participants(
            livekit_room_name=livekit_room_name
        ),
        participants,
    )

    list_participants_mock.assert_requested_once_with(
        ListParticipantsRequest(room=livekit_room_name)
    )


async def test_participant_metadata_updating(
    livekit_mock: LiveKitMock,
    default_livekit_room: Room,
) -> None:
    conference_participant_data: ConferenceParticipantSchema = (
        ConferenceParticipantFactory.build()
    )
    new_participant_metadata: ParticipantMetadataSchema = (
        ParticipantMetadataFactory.build()
    )
    new_participant_info = ParticipantInfo(
        name=conference_participant_data.display_name,
        identity=str(conference_participant_data.user_id),
        metadata=new_participant_metadata.model_dump_metadata_json(),
    )

    update_participant_mock = livekit_mock.route(
        "RoomService",
        "UpdateParticipant",
        new_participant_info,
    )

    assert (
        await conferences_svc.update_participant_metadata(
            livekit_room=default_livekit_room,
            user_id=conference_participant_data.user_id,
            metadata=new_participant_metadata,
        )
        == new_participant_info
    )

    update_participant_mock.assert_requested_once_with(
        UpdateParticipantRequest(
            room=default_livekit_room.name,
            identity=str(conference_participant_data.user_id),
            metadata=new_participant_metadata.model_dump_metadata_json(),
        )
    )


async def test_participant_metadata_updating_participant_not_found(
    faker: Faker,
    livekit_mock: LiveKitMock,
    default_livekit_room: Room,
) -> None:
    user_id: int = faker.random_int(1, 1000)
    new_participant_metadata: ParticipantMetadataSchema = (
        ParticipantMetadataFactory.build()
    )

    update_participant_mock = livekit_mock.route(
        "RoomService",
        "UpdateParticipant",
        side_effect=TwirpError(
            code=TwirpErrorCode.NOT_FOUND,
            msg="participant not found",
            status=status.HTTP_404_NOT_FOUND,
        ),
    )

    assert (
        await conferences_svc.update_participant_metadata(
            livekit_room=default_livekit_room,
            user_id=user_id,
            metadata=new_participant_metadata,
        )
        is None
    )

    update_participant_mock.assert_requested_once_with(
        UpdateParticipantRequest(
            room=default_livekit_room.name,
            identity=str(user_id),
            metadata=new_participant_metadata.model_dump_metadata_json(),
        )
    )
