from collections.abc import Sequence
from typing import Annotated

from tmexio import (
    AsyncServer,
    AsyncSocket,
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
from app.communities.models.participants_db import Participant
from app.communities.rooms import (
    community_room,
    participant_room,
    participants_list_room,
)
from app.communities.store import user_id_to_sids

router = EventRouterExt()


@router.on("list-participants", dependencies=[current_participant_dependency])
async def list_participants(
    community: CommunityById,
    socket: AsyncSocket,
) -> Annotated[
    Sequence[Participant], PydanticPackager(list[Participant.MUBResponseSchema])
]:
    await socket.enter_room(participants_list_room(community.id))
    return await Participant.find_all_by_community_id(community_id=community.id)


@router.on("close-participants")  # TODO no session here
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


@router.on("kick-participant", exceptions=[owner_can_not_be_kicked])
async def kick_participant(
    community: CommunityById,
    target_participant: TargetParticipant,
    server: AsyncServer,
    socket: AsyncSocket,
) -> None:
    if target_participant.is_owner:
        raise owner_can_not_be_kicked

    await target_participant.delete()
    await db.session.commit()

    for sid in user_id_to_sids[target_participant.user_id]:
        await server.leave_room(sid=sid, room=community_room(community.id))
        await server.leave_room(sid=sid, room=participants_list_room(community.id))

    await socket.emit(
        "kicked-from-community",
        {"community_id": community.id},
        target=participant_room(community.id, target_participant.user_id),
        exclude_self=True,
    )
    await server.close_room(participant_room(community.id, target_participant.user_id))

    await socket.emit(
        "delete-participant",
        {"community_id": community.id, "user_id": target_participant.user_id},
        target=participants_list_room(community.id),
        exclude_self=True,
    )


@router.on("transfer-ownership")
async def transfer_ownership(
    community: CommunityById,
    current_participant: CurrentOwner,
    target_participant: TargetParticipant,
    socket: AsyncSocket,
) -> None:
    current_participant.is_owner = False
    target_participant.is_owner = True
    await db.session.commit()

    await socket.emit(
        "update-participation",
        {
            "community_id": community.id,
            "participant": Participant.CurrentSchema.model_validate(
                current_participant
            ).model_dump(mode="json"),
        },
        target=participant_room(community.id, current_participant.user_id),
        exclude_self=True,
    )
    await socket.emit(
        "update-participation",
        {
            "community_id": community.id,
            "participant": Participant.CurrentSchema.model_validate(
                target_participant
            ).model_dump(mode="json"),
        },
        target=participant_room(community.id, target_participant.user_id),
        exclude_self=True,
    )

    await socket.emit(
        "update-participants",
        {
            "community_id": community.id,
            "participants": [
                Participant.ListItemSchema.model_validate(
                    current_participant
                ).model_dump(mode="json"),
                Participant.ListItemSchema.model_validate(
                    target_participant
                ).model_dump(mode="json"),
            ],
        },
        target=participants_list_room(community.id),
        exclude_self=True,
    )
