from livekit.api import TwirpError
from livekit.protocol.models import ParticipantInfo, Room
from starlette import status

from app.common.config import livekit
from app.common.config_bdg import users_internal_bridge
from app.conferences.schemas.conferences_sch import (
    ConferenceParticipantSchema,
    ParticipantMetadataSchema,
    RoomMetadataSchema,
)


async def reactivate_room(livekit_room_name: str) -> Room:
    return await livekit.find_or_create_room(
        room_name=livekit_room_name,
        metadata=RoomMetadataSchema().model_dump_metadata_json(),
    )


async def find_room_by_name(livekit_room_name: str) -> Room | None:
    for room in await livekit.list_rooms(room_names=[livekit_room_name]):
        if room.name == livekit_room_name:
            return room
    return None


async def update_room_metadata(
    livekit_room: Room,
    metadata: RoomMetadataSchema,
) -> Room:
    return await livekit.update_room_metadata(
        room_name=livekit_room.name,
        metadata=metadata.model_dump_metadata_json(),
    )


async def generate_access_token(livekit_room: Room, user_id: int) -> str:
    current_user_profile = await users_internal_bridge.retrieve_user(user_id=user_id)

    return livekit.generate_access_token(
        room_name=livekit_room.name,
        identity=str(user_id),
        name=current_user_profile.display_name,
        metadata=ParticipantMetadataSchema().model_dump_metadata_json(),
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


async def update_participant_metadata(
    livekit_room: Room,
    user_id: int,
    metadata: ParticipantMetadataSchema,
) -> ParticipantInfo | None:
    try:
        return await livekit.update_participant_metadata(
            room_name=livekit_room.name,
            identity=str(user_id),
            metadata=metadata.model_dump_metadata_json(),
        )
    except TwirpError as e:
        if e.status == status.HTTP_404_NOT_FOUND:
            return None
        raise e  # pragma: no cover  # undocumented exceptions from livekit
