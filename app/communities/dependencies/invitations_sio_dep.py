from typing import Annotated

from tmexio import EventException, register_dependency

from app.communities.dependencies.communities_sio_dep import CommunityById
from app.communities.models.invitations_db import Invitation

invitation_not_found = EventException(404, "Invitation not found")


@register_dependency(exceptions=[invitation_not_found])
async def get_invitation_by_ids(
    invitation_id: int,
    community: CommunityById,
) -> Invitation:
    invitation = await Invitation.find_first_by_id(invitation_id)
    if invitation is None or invitation.community_id != community.id:
        raise invitation_not_found
    return invitation


InvitationByIds = Annotated[Invitation, get_invitation_by_ids]
