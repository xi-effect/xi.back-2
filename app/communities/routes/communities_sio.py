from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from typing import Annotated, Any

from tmexio import (
    AsyncServer,
    AsyncSocket,
    EventException,
    EventRouter,
    PydanticPackager,
)

from app.common.config import sessionmaker
from app.common.sqlalchemy_ext import session_context
from app.communities.models.communities_db import Community
from app.communities.models.participants_db import Participant
from app.communities.store import user_id_to_sids

router = EventRouter()


async def user_id_dep(socket: AsyncSocket) -> int:
    session = await socket.get_session()  # TODO better typing!!!
    return session["auth"].user_id  # type: ignore[no-any-return]


@asynccontextmanager
async def db_session() -> AsyncIterator[Any]:
    async with sessionmaker.begin() as session:
        session_context.set(session)
        yield session


@router.on("create-community")
async def create_community(
    data: Community.FullInputSchema,
    socket: AsyncSocket,
) -> Annotated[Community, PydanticPackager(Community.FullResponseSchema)]:
    user_id = await user_id_dep(socket)

    async with db_session():
        community = await Community.create(**data.model_dump())
        await Participant.create(
            community_id=community.id, user_id=user_id, is_owner=True
        )

    await socket.enter_room(f"community-{community.id}")
    await socket.emit(
        "create-community",
        Community.FullResponseSchema.model_validate(community).model_dump(mode="json"),
        target=f"user-{user_id}",
        exclude_self=True,
    )
    return community


community_not_found = EventException(404, "Community not found")
no_community_access = EventException(403, "No access to community")
not_sufficient_permissions = EventException(403, "Not sufficient permissions")


@router.on(
    "update-community",
    exceptions=[community_not_found, no_community_access, not_sufficient_permissions],
)
async def update_community(
    community_id: int,
    data: Community.FullPatchSchema,
    socket: AsyncSocket,
) -> Annotated[Community, PydanticPackager(Community.FullResponseSchema)]:
    user_id = await user_id_dep(socket)

    async with db_session():
        community = await Community.find_first_by_id(community_id)
        if community is None:
            raise community_not_found

        participant = await Participant.find_first_by_kwargs(
            community_id=community.id, user_id=user_id
        )
        if participant is None:
            raise no_community_access
        if not participant.is_owner:
            raise not_sufficient_permissions

        community.update(**data.model_dump(exclude_defaults=True))

    await socket.emit(
        "update-community",
        Community.FullResponseSchema.model_validate(community).model_dump(mode="json"),
        target=f"community-{community_id}",
        exclude_self=True,
    )
    return community


@router.on("retrieve-any-community", exceptions=[community_not_found])
async def retrieve_any_community(
    socket: AsyncSocket,
) -> Annotated[Community, PydanticPackager(Community.FullResponseSchema)]:
    user_id = await user_id_dep(socket)

    async with db_session():
        community = await Participant.find_first_community_by_user_id(user_id=user_id)

    if community is None:
        raise community_not_found

    await socket.enter_room(f"community-{community.id}")
    return community


@router.on("retrieve-community", exceptions=[community_not_found, no_community_access])
async def retrieve_community(
    community_id: int,
    socket: AsyncSocket,
) -> Annotated[Community, PydanticPackager(Community.FullResponseSchema)]:
    user_id = await user_id_dep(socket)

    async with db_session():
        community = await Community.find_first_by_id(community_id)
        if community is None:
            raise community_not_found

        participant = await Participant.find_first_by_kwargs(
            community_id=community.id, user_id=user_id
        )
        if participant is None:
            raise no_community_access

    await socket.enter_room(f"community-{community.id}")
    return community


@router.on("close-community")
async def close_community(community_id: int, socket: AsyncSocket) -> None:
    await socket.leave_room(f"community-{community_id}")


@router.on("list-communities")
async def list_communities(
    socket: AsyncSocket,
) -> Annotated[
    Sequence[Community], PydanticPackager(list[Community.FullResponseSchema])
]:
    user_id = await user_id_dep(socket)

    async with db_session():
        return await Participant.find_all_communities_by_user_id(user_id=user_id)


already_joined = EventException(409, "Already joined")


@router.on("test-join-community", exceptions=[community_not_found, already_joined])
async def test_join_community(
    community_id: int,
    socket: AsyncSocket,
) -> Annotated[Community, PydanticPackager(Community.FullResponseSchema)]:
    user_id = await user_id_dep(socket)

    async with db_session():
        community = await Community.find_first_by_id(community_id)
        if community is None:
            raise community_not_found

        participant = await Participant.find_first_by_kwargs(
            community_id=community.id, user_id=user_id
        )
        if participant is not None:
            raise already_joined
        await Participant.create(
            community_id=community.id, user_id=user_id, is_owner=False
        )

    await socket.enter_room(f"community-{community.id}")
    await socket.emit(
        "join-community",
        Community.FullResponseSchema.model_validate(community).model_dump(mode="json"),
        target=f"user-{user_id}",
        exclude_self=True,
    )
    return community


owner_can_not_leave = EventException(409, "Owner can not leave")


@router.on(
    "leave-community",
    exceptions=[community_not_found, no_community_access, owner_can_not_leave],
)
async def leave_community(
    community_id: int, socket: AsyncSocket, server: AsyncServer
) -> None:
    user_id = await user_id_dep(socket)

    async with db_session():
        community = await Community.find_first_by_id(community_id)
        if community is None:
            raise community_not_found

        participant = await Participant.find_first_by_kwargs(
            community_id=community.id, user_id=user_id
        )
        if participant is None:
            raise no_community_access
        if participant.is_owner:
            raise owner_can_not_leave
        await participant.delete()

    for sid in user_id_to_sids[user_id]:
        await server.leave_room(sid=sid, room=f"community-{community.id}")
    await socket.emit(
        "leave-community",
        {"community_id": community_id},
        target=f"user-{user_id}",
        exclude_self=True,
    )
