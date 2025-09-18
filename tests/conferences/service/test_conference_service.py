import jwt
import pytest
from faker import Faker
from livekit.protocol.models import ParticipantInfo, Room
from livekit.protocol.room import (
    CreateRoomRequest,
    ListParticipantsRequest,
    ListParticipantsResponse,
    ListRoomsRequest,
    ListRoomsResponse,
)
from pydantic_marshals.contains import assert_contains
from respx import MockRouter

from app.common.config import settings
from app.conferences.schemas.conferences_sch import ConferenceParticipantSchema
from app.conferences.services import conferences_svc
from tests.common.livekit_testing import LiveKitMock
from tests.common.respx_ext import assert_last_httpx_request
from tests.common.types import AnyJSON
from tests.conferences.factories import ConferenceParticipantFactory
from tests.factories import UserProfileFactory

pytestmark = pytest.mark.anyio


@pytest.fixture()
async def livekit_room_name(faker: Faker) -> str:
    return faker.user_name()


async def test_room_reactivation(
    livekit_mock: LiveKitMock,
    users_internal_respx_mock: MockRouter,
    livekit_room_name: str,
) -> None:
    livekit_room = Room(name=livekit_room_name)

    create_room_mock = livekit_mock.route("RoomService", "CreateRoom", livekit_room)

    result = await conferences_svc.reactivate_room(livekit_room_name=livekit_room_name)
    assert result == livekit_room

    create_room_mock.assert_requested_once_with(
        CreateRoomRequest(name=livekit_room_name)
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
    users_internal_respx_mock: MockRouter,
    livekit_room_name: str,
    is_room_found: bool,
) -> None:
    livekit_room = Room(name=livekit_room_name) if is_room_found else None

    list_rooms_mock = livekit_mock.route(
        "RoomService",
        "ListRooms",
        ListRoomsResponse(rooms=[] if livekit_room is None else [livekit_room]),
    )

    result = await conferences_svc.find_room_by_name(
        livekit_room_name=livekit_room_name
    )
    assert result == livekit_room

    list_rooms_mock.assert_requested_once_with(
        ListRoomsRequest(names=[livekit_room_name])
    )


async def test_conference_access_token_generation(
    faker: Faker,
    users_internal_respx_mock: MockRouter,
    livekit_room_name: str,
) -> None:
    livekit_room = Room(name=livekit_room_name)

    user_id: int = faker.random_int()
    user_profile_data: AnyJSON = UserProfileFactory.build_json()
    users_internal_bridge_mock = users_internal_respx_mock.get(
        path=f"/users/{user_id}/"
    ).respond(json=user_profile_data)

    access_token = await conferences_svc.generate_access_token(
        livekit_room=livekit_room,
        user_id=user_id,
    )

    assert_contains(
        jwt.decode(access_token, settings.livekit_api_secret, algorithms=["HS256"]),
        {
            "sub": str(user_id),
            "name": user_profile_data["display_name"],
            "video": {"room": livekit_room_name},
        },
    )

    assert_last_httpx_request(
        users_internal_bridge_mock,
        expected_headers={"X-Api-Key": settings.api_key},
    )


async def test_listing_room_participants(
    faker: Faker,
    livekit_mock: LiveKitMock,
    users_internal_respx_mock: MockRouter,
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
