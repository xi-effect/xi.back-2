from typing import Annotated

from fastapi import Depends, Path

from app.common.fastapi_ext import Responses, with_responses
from app.communities.models.roles_db import Role


class RolesResponses(Responses):
    ROLE_NOT_FOUND = 404, "Role not found"


@with_responses(RolesResponses)
async def get_role_by_id(role_id: Annotated[int, Path()]) -> Role:
    role = await Role.find_first_by_id(role_id)
    if role is None:
        raise RolesResponses.ROLE_NOT_FOUND
    return role


RoleByIdDependency = Depends(get_role_by_id)
RoleById = Annotated[Role, RoleByIdDependency]
