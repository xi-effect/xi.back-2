from typing import Annotated

from fastapi import Depends, Path
from livekit.protocol.models import Room
from starlette import status

from app.common.fastapi_ext import Responses, with_responses
from app.conferences.services import conferences_svc


def generate_livekit_room_name_by_classroom_id(
    classroom_id: Annotated[int, Path()],
) -> str:
    return f"classroom-{classroom_id}"


LivekitRoomNameByClassroomID = Annotated[
    str, Depends(generate_livekit_room_name_by_classroom_id)
]


class ConferenceResponses(Responses):
    CONFERENCE_NOT_ACTIVE = status.HTTP_409_CONFLICT, "Conference is not active"


@with_responses(ConferenceResponses)
async def get_livekit_room_by_classroom_id(
    livekit_room_name: LivekitRoomNameByClassroomID,
) -> Room:
    livekit_room = await conferences_svc.find_room_by_name(
        livekit_room_name=livekit_room_name
    )
    if livekit_room is None:
        raise ConferenceResponses.CONFERENCE_NOT_ACTIVE
    return livekit_room


LivekitRoomByClassroomID = Annotated[Room, Depends(get_livekit_room_by_classroom_id)]
