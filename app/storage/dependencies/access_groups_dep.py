from typing import Annotated
from uuid import UUID

from fastapi import Depends, Path

from app.common.fastapi_ext import Responses, with_responses
from app.storage.models.access_groups_db import AccessGroup


class AccessGroupResponses(Responses):
    ACCESS_GROUP_NOT_FOUND = 404, "Access group not found"


@with_responses(AccessGroupResponses)
async def get_access_group_by_id(
    access_group_id: Annotated[UUID, Path()],
) -> AccessGroup:
    access_group = await AccessGroup.find_first_by_id(access_group_id)
    if access_group is None:
        raise AccessGroupResponses.ACCESS_GROUP_NOT_FOUND
    return access_group


AccessGroupById = Annotated[AccessGroup, Depends(get_access_group_by_id)]
