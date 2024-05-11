from collections.abc import Sequence
from typing import Annotated

from tmexio import AsyncServer, AsyncSocket, EventException, PydanticPackager

from app.common.dependencies.authorization_dep import AuthorizedUser
from app.common.sqlalchemy_ext import db
from app.common.tmexio_ext import EventRouterExt
from app.communities.models.communities_db import Community
from app.communities.models.participants_db import Participant
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

    await socket.enter_room(f"community-{community.id}")
    await socket.emit(
        "create-community",
        Community.FullResponseSchema.model_validate(community).model_dump(mode="json"),
        target=f"user-{user.user_id}",
        exclude_self=True,
    )
    return community


community_not_found = EventException(404, "Community not found")
no_community_access = EventException(403, "No access to community")
not_sufficient_permissions = EventException(403, "Not sufficient permissions")


@router.on("retrieve-any-community", exceptions=[community_not_found])
async def retrieve_any_community(
    user: AuthorizedUser,
    socket: AsyncSocket,
) -> Annotated[Community, PydanticPackager(Community.FullResponseSchema)]:
    community = await Participant.find_first_community_by_user_id(user_id=user.user_id)

    if community is None:
        raise community_not_found

    await socket.enter_room(f"community-{community.id}")
    return community


@router.on("retrieve-community", exceptions=[community_not_found, no_community_access])
async def retrieve_community(
    community_id: int,
    user: AuthorizedUser,
    socket: AsyncSocket,
) -> Annotated[Community, PydanticPackager(Community.FullResponseSchema)]:
    community = await Community.find_first_by_id(community_id)
    if community is None:
        raise community_not_found

    participant = await Participant.find_first_by_kwargs(
        community_id=community.id, user_id=user.user_id
    )
    if participant is None:
        raise no_community_access

    await socket.enter_room(f"community-{community.id}")
    return community


@router.on("close-community")  # TODO no session here
async def close_community(community_id: int, socket: AsyncSocket) -> None:
    await socket.leave_room(f"community-{community_id}")


@router.on("list-communities")
async def list_communities(
    user: AuthorizedUser,
) -> Annotated[
    Sequence[Community], PydanticPackager(list[Community.FullResponseSchema])
]:
    return await Participant.find_all_communities_by_user_id(user_id=user.user_id)


already_joined = EventException(409, "Already joined")


@router.on("test-join-community", exceptions=[community_not_found, already_joined])
async def test_join_community(
    community_id: int,
    user: AuthorizedUser,
    socket: AsyncSocket,
) -> Annotated[Community, PydanticPackager(Community.FullResponseSchema)]:
    community = await Community.find_first_by_id(community_id)
    if community is None:
        raise community_not_found

    participant = await Participant.find_first_by_kwargs(
        community_id=community.id, user_id=user.user_id
    )
    if participant is not None:
        raise already_joined

    await Participant.create(
        community_id=community.id, user_id=user.user_id, is_owner=False
    )
    await db.session.commit()

    await socket.enter_room(f"community-{community.id}")
    await socket.emit(
        "join-community",
        Community.FullResponseSchema.model_validate(community).model_dump(mode="json"),
        target=f"user-{user.user_id}",
        exclude_self=True,
    )
    return community


owner_can_not_leave = EventException(409, "Owner can not leave")


@router.on(
    "leave-community",
    exceptions=[community_not_found, no_community_access, owner_can_not_leave],
)
async def leave_community(
    community_id: int, user: AuthorizedUser, socket: AsyncSocket, server: AsyncServer
) -> None:
    community = await Community.find_first_by_id(community_id)
    if community is None:
        raise community_not_found

    participant = await Participant.find_first_by_kwargs(
        community_id=community.id, user_id=user.user_id
    )
    if participant is None:
        raise no_community_access
    if participant.is_owner:
        raise owner_can_not_leave

    await participant.delete()
    await db.session.commit()

    for sid in user_id_to_sids[user.user_id]:
        await server.leave_room(sid=sid, room=f"community-{community.id}")
    await socket.emit(
        "leave-community",
        {"community_id": community_id},
        target=f"user-{user.user_id}",
        exclude_self=True,
    )


@router.on(
    "update-community",
    exceptions=[community_not_found, no_community_access, not_sufficient_permissions],
)
async def update_community(
    community_id: int,
    data: Community.FullPatchSchema,
    user: AuthorizedUser,
    socket: AsyncSocket,
) -> Annotated[Community, PydanticPackager(Community.FullResponseSchema)]:
    community = await Community.find_first_by_id(community_id)
    if community is None:
        raise community_not_found

    participant = await Participant.find_first_by_kwargs(
        community_id=community.id, user_id=user.user_id
    )
    if participant is None:
        raise no_community_access
    if not participant.is_owner:
        raise not_sufficient_permissions

    community.update(**data.model_dump(exclude_defaults=True))
    await db.session.commit()

    await socket.emit(
        "update-community",
        Community.FullResponseSchema.model_validate(community).model_dump(mode="json"),
        target=f"community-{community_id}",
        exclude_self=True,
    )
    return community


@router.on(
    "delete-community",
    exceptions=[community_not_found, not_sufficient_permissions],
)
async def delete_community(
    community_id: int, user: AuthorizedUser, socket: AsyncSocket
) -> None:
    community = await Community.find_first_by_id(community_id)
    if community is None:
        raise community_not_found

    participant = await Participant.find_first_by_kwargs(
        community_id=community.id, user_id=user.user_id
    )
    if participant is None:
        raise no_community_access
    if not participant.is_owner:
        raise not_sufficient_permissions

    await community.delete()
    await db.session.commit()

    await socket.close_room(f"community-{community_id}")
    await socket.emit(
        "delete-community",
        {"community_id": community_id},
        target=f"community-{community_id}",
        exclude_self=True,
    )
