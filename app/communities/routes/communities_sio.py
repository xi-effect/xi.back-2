from collections.abc import Sequence
from typing import Annotated

from tmexio import AsyncServer, AsyncSocket, EventException, PydanticPackager

from app.common.dependencies.authorization_dep import AuthorizedUser
from app.common.sqlalchemy_ext import db
from app.common.tmexio_ext import EventRouterExt
from app.communities.dependencies.communities_sio_dep import (
    CommunityById,
    CurrentParticipant,
    community_not_found,
    current_owner_dependency,
)
from app.communities.models.communities_db import Community
from app.communities.models.participants_db import Participant
from app.communities.rooms import (
    community_room,
    participant_room,
    participants_list_room,
    user_room,
)
from app.communities.store import user_id_to_sids

router = EventRouterExt()


@router.on("create-community")
async def create_community(
    data: Community.FullInputSchema,
    user: AuthorizedUser,
    socket: AsyncSocket,
) -> Annotated[Community, PydanticPackager(Community.FullResponseSchema)]:
    community = await Community.create(**data.model_dump())
    await Participant.create(
        community_id=community.id, user_id=user.user_id, is_owner=True
    )
    await db.session.commit()

    await socket.enter_room(community_room(community.id))
    await socket.enter_room(participant_room(community.id, user.user_id))
    await socket.emit(
        "create-community",
        Community.FullResponseSchema.model_validate(community).model_dump(mode="json"),
        target=user_room(user.user_id),
        exclude_self=True,
    )
    return community


@router.on("retrieve-any-community", exceptions=[community_not_found])
async def retrieve_any_community(
    user: AuthorizedUser,
    socket: AsyncSocket,
) -> Annotated[Community, PydanticPackager(Community.FullResponseSchema)]:
    result = await Participant.find_first_community_by_user_id(user_id=user.user_id)
    if result is None:
        raise community_not_found

    community, participant = result

    await socket.enter_room(community_room(community.id))
    await socket.enter_room(participant_room(community.id, user.user_id))
    return community


@router.on("retrieve-community")
async def retrieve_community(
    community: CommunityById,
    participant: CurrentParticipant,
    socket: AsyncSocket,
) -> Annotated[Community, PydanticPackager(Community.FullResponseSchema)]:
    await socket.enter_room(community_room(community.id))
    await socket.enter_room(participant_room(community.id, participant.user_id))
    return community


@router.on("close-community")  # TODO no session here
async def close_community(
    community_id: int, user: AuthorizedUser, socket: AsyncSocket
) -> None:
    await socket.leave_room(community_room(community_id))
    await socket.leave_room(participants_list_room(community_id))
    await socket.leave_room(participant_room(community_id, user.user_id))


@router.on("list-communities")
async def list_communities(
    user: AuthorizedUser,
) -> Annotated[
    Sequence[Community], PydanticPackager(list[Community.FullResponseSchema])
]:
    return await Participant.find_all_communities_by_user_id(user_id=user.user_id)


already_joined = EventException(409, "Already joined")


@router.on("test-join-community", exceptions=[already_joined])
async def test_join_community(
    community: CommunityById,
    user: AuthorizedUser,
    socket: AsyncSocket,
) -> Annotated[Community, PydanticPackager(Community.FullResponseSchema)]:
    participant = await Participant.find_first_by_kwargs(
        community_id=community.id, user_id=user.user_id
    )
    if participant is not None:
        raise already_joined

    participant = await Participant.create(
        community_id=community.id, user_id=user.user_id, is_owner=False
    )
    await db.session.commit()

    await socket.enter_room(community_room(community.id))
    await socket.enter_room(participant_room(community.id, user.user_id))

    await socket.emit(
        "join-community",
        Community.FullResponseSchema.model_validate(community).model_dump(mode="json"),
        target=user_room(user.user_id),
        exclude_self=True,
    )

    await socket.emit(
        "create-participant",
        Participant.FullResponseSchema.model_validate(participant).model_dump(
            mode="json"
        ),
        target=participants_list_room(community.id),
        exclude_self=True,
    )
    return community


owner_can_not_leave = EventException(409, "Owner can not leave")


@router.on("leave-community", exceptions=[owner_can_not_leave])
async def leave_community(
    community: CommunityById,
    participant: CurrentParticipant,
    user: AuthorizedUser,
    socket: AsyncSocket,
    server: AsyncServer,
) -> None:
    if participant.is_owner:
        raise owner_can_not_leave

    await participant.delete()
    await db.session.commit()

    for sid in user_id_to_sids[user.user_id]:
        await server.leave_room(sid=sid, room=community_room(community.id))
        await server.leave_room(sid=sid, room=participants_list_room(community.id))

    await socket.emit(
        "leave-community",
        {"community_id": community.id},
        target=participant_room(community.id, participant.user_id),
        exclude_self=True,
    )
    await socket.close_room(participant_room(community.id, participant.user_id))

    await socket.emit(
        "delete-participant",
        {"community_id": community.id, "participant_id": participant.id},
        target=participants_list_room(community.id),
        exclude_self=True,
    )


@router.on("update-community", dependencies=[current_owner_dependency])
async def update_community(
    data: Community.FullPatchSchema,
    community: CommunityById,
    socket: AsyncSocket,
) -> Annotated[Community, PydanticPackager(Community.FullResponseSchema)]:
    community.update(**data.model_dump(exclude_defaults=True))
    await db.session.commit()

    await socket.emit(
        "update-community",
        Community.FullResponseSchema.model_validate(community).model_dump(mode="json"),
        target=community_room(community.id),
        exclude_self=True,
    )
    return community


@router.on("delete-community", dependencies=[current_owner_dependency])
async def delete_community(community: CommunityById, socket: AsyncSocket) -> None:
    await community.delete()
    await db.session.commit()

    await socket.emit(
        "delete-community",
        {"community_id": community.id},
        target=community_room(community.id),
        exclude_self=True,
    )

    await socket.close_room(community_room(community.id))
    await socket.close_room(participants_list_room(community.id))
    # TODO close all `participant-{community_id}-{user_id}` rooms (bg task?)
