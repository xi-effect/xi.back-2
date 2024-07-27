from collections.abc import Sequence
from typing import Annotated

from pydantic import BaseModel, ConfigDict
from tmexio import (
    AsyncServer,
    AsyncSocket,
    Emitter,
    EventException,
    PydanticPackager,
    register_dependency,
)

from app.common.sqlalchemy_ext import db
from app.common.tmexio_ext import EventRouterExt
from app.communities.dependencies.communities_sio_dep import (
    CommunityById,
    CurrentOwner,
    current_participant_dependency,
)
from app.communities.models.communities_db import CommunityIdSchema
from app.communities.models.participants_db import Participant
from app.communities.rooms import (
    community_room,
    participant_room,
    participants_list_room,
)
from app.communities.store import user_id_to_sids

router = EventRouterExt(tags=["participants-list"])


CreateParticipantEmitter = Annotated[
    Emitter[Participant],
    router.register_server_emitter(
        Participant.ServerEventSchema,
        event_name="create-participant",
        summary="A user has joined the current community",
    ),
]

UpdateParticipationEmitter = Annotated[
    Emitter[Participant],
    router.register_server_emitter(
        Participant.ServerEventSchema,
        event_name="update-participation",
        summary="Current participant's data has been updated",
    ),
]


class UpdateParticipantsServerSchema(BaseModel):
    community_id: int
    participants: list[Participant.ListItemSchema]


class UpdateParticipantsPreSchema(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    community_id: int
    participants: list[Participant]


UpdateParticipantsEmitter = Annotated[
    Emitter[UpdateParticipantsPreSchema],
    router.register_server_emitter(
        UpdateParticipantsServerSchema,
        event_name="update-participants",
        summary="Participants' metadata has been updated in the current community",
    ),
]


DeleteParticipantEmitter = Annotated[
    Emitter[Participant],
    router.register_server_emitter(
        Participant.IDsSchema,
        event_name="delete-participant",
        summary="A user has left or has been kicked from the current community",
    ),
]

KickedFromCommunityEmitter = Annotated[
    Emitter[CommunityIdSchema],
    router.register_server_emitter(
        CommunityIdSchema,
        event_name="kicked-from-community",
        summary="Current participant has been kicked from the current community",
    ),
]


@router.on(
    "list-participants",
    summary="Open the list of participants of a community",
    dependencies=[current_participant_dependency],
)
async def list_participants(
    community: CommunityById,
    socket: AsyncSocket,
) -> Annotated[
    Sequence[Participant], PydanticPackager(list[Participant.MUBResponseSchema])
]:
    await socket.enter_room(participants_list_room(community.id))
    return await Participant.find_all_by_community_id(community_id=community.id)


@router.on(
    "close-participants",
    summary="Close the list of participants of a community",
)  # TODO no session here
async def close_participants(community_id: int, socket: AsyncSocket) -> None:
    await socket.leave_room(participants_list_room(community_id))


target_is_the_source = EventException(409, "Target is the source")
participant_not_found = EventException(404, "Participant not found")
owner_can_not_be_kicked = EventException(403, "Owner can not be kicked")


@register_dependency(exceptions=[target_is_the_source, participant_not_found])
async def target_participant_dependency(
    community: CommunityById,
    current_participant: CurrentOwner,
    target_user_id: int,
) -> Participant:
    if current_participant.user_id == target_user_id:
        raise target_is_the_source

    target_participant = await Participant.find_first_by_kwargs(
        community_id=community.id, user_id=target_user_id
    )
    if target_participant is None:
        raise participant_not_found
    return target_participant


TargetParticipant = Annotated[Participant, target_participant_dependency]


@router.on(
    "kick-participant",
    summary="Kick a participant from a community",
    exceptions=[owner_can_not_be_kicked],
)
async def kick_participant(
    community: CommunityById,
    target_participant: TargetParticipant,
    server: AsyncServer,
    kicked_from_community_emitter: KickedFromCommunityEmitter,
    delete_participant_emitter: DeleteParticipantEmitter,
) -> None:
    if target_participant.is_owner:
        raise owner_can_not_be_kicked

    await target_participant.delete()
    await db.session.commit()

    for sid in user_id_to_sids[target_participant.user_id]:
        await server.leave_room(sid=sid, room=community_room(community.id))
        await server.leave_room(sid=sid, room=participants_list_room(community.id))

    await kicked_from_community_emitter.emit(
        CommunityIdSchema(community_id=community.id),
        target=participant_room(community.id, target_participant.user_id),
        exclude_self=True,
    )
    await server.close_room(participant_room(community.id, target_participant.user_id))

    await delete_participant_emitter.emit(
        target_participant,
        target=participants_list_room(community.id),
        exclude_self=True,
    )


@router.on("transfer-ownership", summary="Transfer ownership of the community")
async def transfer_ownership(
    community: CommunityById,
    current_participant: CurrentOwner,
    target_participant: TargetParticipant,
    update_participation_emitter: UpdateParticipationEmitter,
    update_participants_emitter: UpdateParticipantsEmitter,
) -> None:
    current_participant.is_owner = False
    target_participant.is_owner = True
    await db.session.commit()

    await update_participation_emitter.emit(
        current_participant,
        target=participant_room(community.id, current_participant.user_id),
        exclude_self=True,
    )
    await update_participation_emitter.emit(
        target_participant,
        target=participant_room(community.id, target_participant.user_id),
        exclude_self=True,
    )

    await update_participants_emitter.emit(
        UpdateParticipantsPreSchema(
            community_id=community.id,
            participants=[current_participant, target_participant],
        ),
        target=participants_list_room(community.id),
        exclude_self=True,
    )
