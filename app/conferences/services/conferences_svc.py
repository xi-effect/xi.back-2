from livekit.protocol.models import Room

from app.common.config import livekit
from app.common.config_bdg import users_internal_bridge
from app.conferences.schemas.conferences_sch import ConferenceParticipantSchema


async def reactivate_room(livekit_room_name: str) -> Room:
    return await livekit.find_or_create_room(room_name=livekit_room_name)


async def find_room_by_name(livekit_room_name: str) -> Room | None:
    for room in await livekit.list_rooms(room_names=[livekit_room_name]):
        if room.name == livekit_room_name:
            return room
    return None


async def generate_access_token(livekit_room: Room, user_id: int) -> str:
    current_user_profile = await users_internal_bridge.retrieve_user(user_id=user_id)

    return livekit.generate_access_token(
        identity=str(user_id),
        name=current_user_profile.display_name,
        room_name=livekit_room.name,
    )


async def list_room_participants(
    livekit_room_name: str,
) -> list[ConferenceParticipantSchema]:
    return [
        ConferenceParticipantSchema(
            user_id=participant.identity,
            display_name=participant.name,
        )
        for participant in await livekit.list_room_participants(
            room_name=livekit_room_name
        )
    ]
