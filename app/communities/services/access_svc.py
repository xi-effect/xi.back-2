from app.common.schemas.storage_sch import YDocAccessLevel
from app.communities.models.participants_db import Participant


async def retrieve_community_access_level(
    community_id: int, user_id: int
) -> YDocAccessLevel:
    participant = await Participant.find_first_by_kwargs(
        community_id=community_id, user_id=user_id
    )
    if participant is None:
        return YDocAccessLevel.NO_ACCESS
    if participant.is_owner:
        return YDocAccessLevel.READ_WRITE
    return YDocAccessLevel.READ_ONLY
