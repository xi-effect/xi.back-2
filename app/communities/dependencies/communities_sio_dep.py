from typing import Annotated

from tmexio import EventException, register_dependency

from app.common.dependencies.authorization_sio_dep import AuthorizedUser
from app.communities.models.communities_db import Community
from app.communities.models.participants_db import Participant

community_not_found = EventException(404, "Community not found")


@register_dependency(exceptions=[community_not_found])
async def community_by_id_dependency(community_id: int) -> Community:
    community = await Community.find_first_by_id(community_id)
    if community is None:
        raise community_not_found
    return community


CommunityById = Annotated[Community, community_by_id_dependency]

no_community_access = EventException(403, "No access to community")


@register_dependency(exceptions=[no_community_access])
async def current_participant_dependency(
    community: CommunityById, user: AuthorizedUser
) -> Participant:
    participant = await Participant.find_first_by_kwargs(
        community_id=community.id, user_id=user.user_id
    )
    if participant is None:
        raise no_community_access
    return participant


CurrentParticipant = Annotated[Participant, current_participant_dependency]

not_sufficient_permissions = EventException(403, "Not sufficient permissions")


@register_dependency(exceptions=[not_sufficient_permissions])
async def current_owner_dependency(participant: CurrentParticipant) -> Participant:
    if not participant.is_owner:
        raise not_sufficient_permissions
    return participant


CurrentOwner = Annotated[Participant, current_owner_dependency]
