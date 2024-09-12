from collections.abc import Sequence

from app.common.fastapi_ext import APIRouterExt
from app.communities.dependencies.communities_dep import CommunityById
from app.communities.dependencies.roles_dep import RoleById
from app.communities.models.roles_db import Permission, Role, RolePermission

router = APIRouterExt(tags=["roles mub"])


@router.get(
    "/communities/{community_id}/roles/",
    response_model=list[Role.ItemSchema],
    summary="List roles in the community",
)
async def list_roles(
    community: CommunityById,
    offset: int,
    limit: int,
) -> Sequence[Role]:
    return await Role.find_paginated_by_community_id(community.id, offset, limit)


@router.post(
    "/communities/{community_id}/roles/",
    status_code=201,
    response_model=Role.ItemSchema,
    summary="Create a new role in the community",
)
async def create_role(community: CommunityById, data: Role.InputSchema) -> Role:
    return await Role.create(community_id=community.id, **data.model_dump())


@router.get(
    "/roles/{role_id}/",
    response_model=Role.ResponseSchema,
    summary="Retrieve any role by id",
)
async def retrieve_role(role: RoleById) -> Role:
    return role


class UpdateRoleSchema(Role.PatchSchema):
    # TODO https://github.com/niqzart/pydantic-marshals/issues/32
    permissions: list[Permission]


@router.patch(
    "/roles/{role_id}/",
    response_model=Role.ResponseSchema,
    summary="Update any role by id",
)
async def patch_role(
    role: RoleById,
    role_data: UpdateRoleSchema,
) -> Role:
    role.update(
        **role_data.model_dump(exclude={"permissions"}),
        permissions=await RolePermission.modify_role_permissions(
            role_id=role.id,
            current_permissions=[r.permission for r in role.permissions],
            patch_permissions=role_data.permissions,
        ),
    )
    return role


@router.delete(
    "/roles/{role_id}/",
    status_code=204,
    summary="Delete any role by id",
)
async def delete_role(role: RoleById) -> None:
    await role.delete()
