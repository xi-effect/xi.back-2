from collections.abc import Sequence
from typing import Annotated

from tmexio import EventException, PydanticPackager

from app.common.dependencies.authorization_sio_dep import AuthorizedUser
from app.common.sqlalchemy_ext import db
from app.common.tmexio_ext import EventRouterExt
from app.communities.dependencies.communities_sio_dep import (
    CommunityById,
    current_owner_dependency,
)
from app.communities.dependencies.invitations_sio_dep import InvitationByIds
from app.communities.models.invitations_db import Invitation

# TODO mb add invitations_list_room
# TODO real permissions checks
router = EventRouterExt(
    tags=["invitations-list"],
    dependencies=[current_owner_dependency],
)


@router.on("list-invitations", summary="List invitations in the community")
async def list_invitations(
    community: CommunityById,
) -> Annotated[Sequence[Invitation], PydanticPackager(list[Invitation.ResponseSchema])]:
    return await Invitation.find_all_valid_by_community_id(community_id=community.id)


quantity_exceeded = EventException(409, "Quantity exceeded")


@router.on(
    "create-invitation",
    summary="Create a new invitation in the community",
    exceptions=[quantity_exceeded],
)
async def create_invitation(
    data: Invitation.InputSchema,
    community: CommunityById,
    user: AuthorizedUser,
) -> Annotated[Invitation, PydanticPackager(Invitation.ResponseSchema)]:
    if await Invitation.count_by_community_id(community.id) >= Invitation.max_count:
        raise quantity_exceeded

    invitation = await Invitation.create(
        community_id=community.id,
        creator_id=user.user_id,
        **data.model_dump(),
    )
    await db.session.commit()

    # notify subscribers here

    return invitation


@router.on("delete-invitation", summary="Delete any invitation by id")
async def delete_invitation(invitation: InvitationByIds) -> None:
    await invitation.delete()
