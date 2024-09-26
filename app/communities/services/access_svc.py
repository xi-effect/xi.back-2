from app.common.access import AccessLevel
from app.communities.models.participants_db import Participant


async def retrieve_community_access_level(
    community_id: int, user_id: int
) -> AccessLevel:
    participant = await Participant.find_first_by_kwargs(
        community_id=community_id, user_id=user_id
    )
    if participant is None:
        return AccessLevel.NO_ACCESS
    if participant.is_owner:
        return AccessLevel.READ_WRITE
    return AccessLevel.READ_ONLY
