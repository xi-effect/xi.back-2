from collections.abc import Sequence

from app.common.fastapi_ext import APIRouterExt
from app.communities.dependencies.communities_dep import CommunityById
from app.communities.dependencies.invitations_dep import InvitationById
from app.communities.models.invitations_db import Invitation
from app.communities.responses import LimitedListResponses

router = APIRouterExt(tags=["invitations mub"])


@router.get(
    "/communities/{community_id}/invitations/",
    response_model=list[Invitation.FullResponseSchema],
    summary="List invitations for the community",
)
async def list_invitations(community: CommunityById) -> Sequence[Invitation]:
    return await Invitation.find_all_by_kwargs(  # TODO (35581079) pragma: no cover
        Invitation.created_at,
        community_id=community.id,
    )


@router.post(
    "/communities/{community_id}/invitations/",
    status_code=201,
    response_model=Invitation.FullResponseSchema,
    responses=LimitedListResponses.responses(),
    summary="Create a new invitation for the community",
)
async def create_invitation(
    community: CommunityById, data: Invitation.FullInputSchema
) -> Invitation:
    if await Invitation.count_by_community_id(community.id) >= Invitation.max_count:
        raise LimitedListResponses.QUANTITY_EXCEEDED
    return await Invitation.create(
        community_id=community.id,
        **data.model_dump(),
    )


@router.get(
    "/invitations/{invitation_id}/",
    response_model=Invitation.FullResponseSchema,
    summary="Retrieve any invitation by id",
)
async def retrieve_invitation(invitation: InvitationById) -> Invitation:
    return invitation


@router.delete(
    "/invitations/{invitation_id}/",
    status_code=204,
    summary="Delete any invitation by id",
)
async def delete_invitation(invitation: InvitationById) -> None:
    await invitation.delete()
