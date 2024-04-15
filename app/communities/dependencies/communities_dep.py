from typing import Annotated

from fastapi import Depends, Path

from app.common.fastapi_ext import Responses, with_responses
from app.communities.models.communities_db import Community


class CommunityResponses(Responses):
    COMMUNITY_NOT_FOUND = 404, "Community not found"


@with_responses(CommunityResponses)
async def get_community_by_id(community_id: Annotated[int, Path()]) -> Community:
    community = await Community.find_first_by_id(community_id)
    if community is None:
        raise CommunityResponses.COMMUNITY_NOT_FOUND
    return community


CommunityByIdDependency = Depends(get_community_by_id)
CommunityById = Annotated[Community, CommunityByIdDependency]
