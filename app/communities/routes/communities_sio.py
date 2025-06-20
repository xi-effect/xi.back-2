from collections.abc import Sequence
from typing import Annotated

from pydantic_marshals.base import CompositeMarshalModel
from starlette import status
from tmexio import AsyncServer, AsyncSocket, Emitter, EventException, PydanticPackager

from app.common.dependencies.authorization_sio_dep import AuthorizedUser
from app.common.sqlalchemy_ext import db
from app.common.tmexio_ext import EventRouterExt
from app.communities.dependencies.communities_sio_dep import (
    CommunityById,
    CurrentParticipant,
    community_not_found,
    current_owner_dependency,
)
from app.communities.dependencies.invitations_sio_dep import invitation_not_found
from app.communities.models.communities_db import Community, CommunityIdSchema
from app.communities.models.invitations_db import Invitation
from app.communities.models.participants_db import Participant
from app.communities.rooms import (
    community_room,
    participant_room,
    participants_list_room,
    user_room,
)
from app.communities.routes.participants_sio import (
    CreateParticipantEmitter,
    DeleteParticipantEmitter,
)
from app.communities.store import user_id_to_sids

router = EventRouterExt(tags=["communities-all"])  # TODO split community routers


class ParticipationSchema(CompositeMarshalModel):
    community: Annotated[Community, Community.FullResponseSchema]
    participant: Annotated[Participant, Participant.CurrentSchema]


ParticipationSchemaAck = Annotated[
    ParticipationSchema, PydanticPackager(ParticipationSchema.build_marshal())
]


@router.on(
    "create-community",
    summary="Create and open a new community",
    server_summary="A community has been created by the current user",
)
async def create_community(
    data: Community.FullInputSchema,
    user: AuthorizedUser,
    socket: AsyncSocket,
    duplex_emitter: Annotated[Emitter[Community], Community.FullResponseSchema],
) -> ParticipationSchemaAck:
    community = await Community.create(**data.model_dump())
    participant = await Participant.create(
        community_id=community.id, user_id=user.user_id, is_owner=True
    )
    await db.session.commit()

    await socket.enter_room(community_room(community.id))
    await socket.enter_room(participant_room(community.id, user.user_id))
    await duplex_emitter.emit(
        community,
        target=user_room(user.user_id),
        exclude_self=True,
    )

    return ParticipationSchema(community=community, participant=participant)


@router.on(
    "retrieve-any-community",
    summary="Retrieve and open any joined community",
    exceptions=[community_not_found],
)
async def retrieve_any_community(
    user: AuthorizedUser,
    socket: AsyncSocket,
) -> ParticipationSchemaAck:
    result = await Participant.find_first_community_by_user_id(user_id=user.user_id)
    if result is None:
        raise community_not_found

    community, participant = result

    await socket.enter_room(community_room(community.id))
    await socket.enter_room(participant_room(community.id, user.user_id))
    return ParticipationSchema(community=community, participant=participant)


@router.on("retrieve-community", summary="Retrieve and open a community by id")
async def retrieve_community(
    community: CommunityById,
    participant: CurrentParticipant,
    socket: AsyncSocket,
) -> ParticipationSchemaAck:
    await socket.enter_room(community_room(community.id))
    await socket.enter_room(participant_room(community.id, participant.user_id))
    return ParticipationSchema(community=community, participant=participant)


@router.on("close-community", summary="Close a community")  # TODO no session here
async def close_community(
    community_id: int, user: AuthorizedUser, socket: AsyncSocket
) -> None:
    await socket.leave_room(community_room(community_id))
    await socket.leave_room(participants_list_room(community_id))
    await socket.leave_room(participant_room(community_id, user.user_id))


@router.on("list-communities", summary="List all joined communities")
async def list_communities(
    user: AuthorizedUser,
) -> Annotated[
    Sequence[Community], PydanticPackager(list[Community.FullResponseSchema])
]:
    return await Participant.find_all_communities_by_user_id(user_id=user.user_id)


already_joined = EventException(status.HTTP_409_CONFLICT, "Already joined")


@router.on(
    "join-community",
    summary="Join and open a community using an invitation",
    server_summary="The current user has joined a community",
    exceptions=[invitation_not_found, already_joined],
)
async def join_community(
    code: str,
    user: AuthorizedUser,
    socket: AsyncSocket,
    create_participant_emitter: CreateParticipantEmitter,
    duplex_emitter: Annotated[Emitter[Community], Community.FullResponseSchema],
) -> ParticipationSchemaAck:
    result = await Invitation.find_with_community_by_code(code)
    if result is None:
        raise invitation_not_found
    community, invitation = result

    if not invitation.is_valid():
        # TODO delete invitation (errors do a rollback)
        raise invitation_not_found

    participant = await Participant.find_first_by_kwargs(
        community_id=community.id, user_id=user.user_id
    )
    if participant is not None:
        raise already_joined

    participant = await Participant.create(
        community_id=community.id, user_id=user.user_id, is_owner=False
    )
    invitation.usage_count += 1
    await db.session.commit()

    await socket.enter_room(community_room(community.id))
    await socket.enter_room(participant_room(community.id, user.user_id))

    await duplex_emitter.emit(
        community,
        target=user_room(user.user_id),
        exclude_self=True,
    )

    await create_participant_emitter.emit(
        participant,
        target=participants_list_room(community.id),
        exclude_self=True,
    )

    return ParticipationSchema(community=community, participant=participant)


owner_can_not_leave = EventException(status.HTTP_409_CONFLICT, "Owner can not leave")


@router.on(
    "leave-community",
    summary="Leave any community by id",
    server_summary="The current participant has left the current community",
    exceptions=[owner_can_not_leave],
)
async def leave_community(
    community: CommunityById,
    participant: CurrentParticipant,
    user: AuthorizedUser,
    socket: AsyncSocket,
    server: AsyncServer,
    delete_participant_emitter: DeleteParticipantEmitter,
    duplex_emitter: Emitter[CommunityIdSchema],
) -> None:
    if participant.is_owner:
        raise owner_can_not_leave

    await participant.delete()
    await db.session.commit()

    for sid in user_id_to_sids[user.user_id]:
        await server.leave_room(sid=sid, room=community_room(community.id))
        await server.leave_room(sid=sid, room=participants_list_room(community.id))

    await duplex_emitter.emit(
        CommunityIdSchema(community_id=community.id),
        target=participant_room(community.id, participant.user_id),
        exclude_self=True,
    )
    await socket.close_room(participant_room(community.id, participant.user_id))

    await delete_participant_emitter.emit(
        participant,
        target=participants_list_room(community.id),
        exclude_self=True,
    )


@router.on(
    "update-community",
    summary="Update any community's metadata by id",
    server_summary="Current community's metadata has been updated",
    dependencies=[current_owner_dependency],
)
async def update_community(
    data: Community.FullPatchSchema,
    community: CommunityById,
    duplex_emitter: Annotated[Emitter[Community], Community.FullResponseSchema],
) -> Annotated[Community, PydanticPackager(Community.FullResponseSchema)]:
    community.update(**data.model_dump(exclude_defaults=True))
    await db.session.commit()

    await duplex_emitter.emit(
        community,
        target=community_room(community.id),
        exclude_self=True,
    )
    return community


@router.on(
    "delete-community",
    summary="Delete any community by id",
    server_summary="Current community has been deleted",
    dependencies=[current_owner_dependency],
)
async def delete_community(
    community: CommunityById,
    socket: AsyncSocket,
    duplex_emitter: Emitter[CommunityIdSchema],
) -> None:
    await community.delete()
    await db.session.commit()

    await duplex_emitter.emit(
        CommunityIdSchema(community_id=community.id),
        target=community_room(community.id),
        exclude_self=True,
    )

    await socket.close_room(community_room(community.id))
    await socket.close_room(participants_list_room(community.id))
    # TODO close all `participant-{community_id}-{user_id}` rooms (bg task?)
