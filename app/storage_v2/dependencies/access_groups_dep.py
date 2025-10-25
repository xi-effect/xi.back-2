from typing import Annotated
from uuid import UUID

from fastapi import Depends, Path
from starlette import status

from app.common.fastapi_ext import Responses, with_responses
from app.storage_v2.models.access_groups_db import AccessGroup


class AccessGroupResponses(Responses):
    ACCESS_GROUP_NOT_FOUND = status.HTTP_404_NOT_FOUND, "Access group not found"


@with_responses(AccessGroupResponses)
async def get_access_group_by_id(
    access_group_id: Annotated[UUID, Path()],
) -> AccessGroup:
    access_group = await AccessGroup.find_first_by_id(access_group_id)
    if access_group is None:
        raise AccessGroupResponses.ACCESS_GROUP_NOT_FOUND
    return access_group


AccessGroupByID = Annotated[AccessGroup, Depends(get_access_group_by_id)]
