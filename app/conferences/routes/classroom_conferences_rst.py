from typing import Annotated

from fastapi import Path
from starlette import status

from app.common.config_bdg import classrooms_bridge, notifications_bridge
from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt, Responses
from app.common.schemas.notifications_sch import (
    ClassroomNotificationPayloadSchema,
    NotificationInputSchema,
    NotificationKind,
)
from app.conferences.dependencies.conferences_dep import (
    LivekitRoomByClassroomID,
    LivekitRoomNameByClassroomID,
)
from app.conferences.schemas.conferences_sch import (
    ConferenceParticipantSchema,
    ParticipantMetadataSchema,
    RoomMetadataSchema,
)
from app.conferences.services import conferences_svc

router = APIRouterExt(tags=["classroom conferences"])


@router.post(
    path="/roles/tutor/classrooms/{classroom_id}/conference/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Reactivate a conference in a classroom by id",
)
async def reactivate_classroom_conference(
    classroom_id: Annotated[int, Path()],
    livekit_room_name: LivekitRoomNameByClassroomID,
) -> None:
    await conferences_svc.reactivate_room(livekit_room_name=livekit_room_name)

    # TODO: make notifications service know classrooms instead
    classroom_student_ids = await classrooms_bridge.list_classroom_student_ids(
        classroom_id=classroom_id
    )
    if len(classroom_student_ids) == 0:
        return

    await notifications_bridge.send_notification(
        NotificationInputSchema(
            payload=ClassroomNotificationPayloadSchema(
                kind=NotificationKind.CLASSROOM_CONFERENCE_STARTED_V1,
                classroom_id=classroom_id,
            ),
            recipient_user_ids=classroom_student_ids,
        )
    )


@router.put(
    path="/roles/tutor/classrooms/{classroom_id}/conference/metadata/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Update metadata of a conference in a classroom by id",
)
async def update_classroom_conference_metadata(
    livekit_room: LivekitRoomByClassroomID,
    metadata: RoomMetadataSchema,
) -> None:
    await conferences_svc.update_room_metadata(
        livekit_room=livekit_room,
        metadata=metadata,
    )


@router.post(
    path="/roles/tutor/classrooms/{classroom_id}/conference/access-tokens/",
    summary="Create a tutor access token for a conference in a classroom by id",
)
@router.post(  # TODO split this if token grants will become different
    path="/roles/student/classrooms/{classroom_id}/conference/access-tokens/",
    summary="Create a student access token for a conference in a classroom by id",
)
async def generate_classroom_conference_access_token(
    livekit_room: LivekitRoomByClassroomID,
    auth_data: AuthorizationData,
) -> str:
    return await conferences_svc.generate_access_token(
        livekit_room=livekit_room,
        user_id=auth_data.user_id,
    )


@router.get(
    path="/roles/tutor/classrooms/{classroom_id}/conference/participants/",
    summary="List conference participants for a classroom by id",
)
@router.get(
    path="/roles/student/classrooms/{classroom_id}/conference/participants/",
    summary="List conference participants for a classroom by id",
)
async def list_classroom_conference_participants(
    livekit_room: LivekitRoomByClassroomID,
) -> list[ConferenceParticipantSchema]:
    return await conferences_svc.list_room_participants(
        livekit_room_name=livekit_room.name
    )


class ConferenceParticipantResponses(Responses):
    CONFERENCE_PARTICIPANT_NOT_FOUND = (
        status.HTTP_404_NOT_FOUND,
        "Conference participant not found",
    )


@router.put(
    path="/roles/tutor/classrooms/{classroom_id}/conference/participants/current/metadata/",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=ConferenceParticipantResponses.responses(),
    summary="Update metadata of the current participant of a conference in a classroom by id",
)
@router.put(  # TODO split this if metadata will become different
    path="/roles/student/classrooms/{classroom_id}/conference/participants/current/metadata/",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=ConferenceParticipantResponses.responses(),
    summary="Update metadata of the current participant of a conference in a classroom by id",
)
async def update_classroom_conference_current_participant_metadata(
    auth_data: AuthorizationData,
    livekit_room: LivekitRoomByClassroomID,
    metadata: ParticipantMetadataSchema,
) -> None:
    participant_info = await conferences_svc.update_participant_metadata(
        livekit_room=livekit_room,
        user_id=auth_data.user_id,
        metadata=metadata,
    )
    if participant_info is None:
        raise ConferenceParticipantResponses.CONFERENCE_PARTICIPANT_NOT_FOUND


@router.put(
    path="/roles/tutor/classrooms/{classroom_id}/conference/participants/{participant_user_id}/metadata/",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=ConferenceParticipantResponses.responses(),
    summary="Update metadata of a participant of a conference in a classroom by ids",
)
async def update_classroom_conference_other_participant_metadata(
    livekit_room: LivekitRoomByClassroomID,
    participant_user_id: int,
    metadata: ParticipantMetadataSchema,
) -> None:
    participant_info = await conferences_svc.update_participant_metadata(
        livekit_room=livekit_room,
        user_id=participant_user_id,
        metadata=metadata,
    )
    if participant_info is None:
        raise ConferenceParticipantResponses.CONFERENCE_PARTICIPANT_NOT_FOUND
