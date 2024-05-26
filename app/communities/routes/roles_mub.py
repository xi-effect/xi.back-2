from collections.abc import Sequence

from app.common.fastapi_ext import APIRouterExt
from app.communities.dependencies.communities_dep import CommunityById
from app.communities.dependencies.roles_dep import RoleById
from app.communities.models.roles_db import Permission, Role, RolePermission

router = APIRouterExt(tags=["roles meta mub"])


@router.post(
    "/communities/{community_id}/roles/",
    status_code=201,
    response_model=Role.ResponseSchema,
    summary="Create a new role in the community",
)
async def create_role(community: CommunityById, data: Role.InputSchema) -> Role:
    return await Role.create(community_id=community.id, **data.model_dump())


@router.get(
    "/communities/{community_id}/roles/",
    response_model=list[Role.ResponseSchema],
    summary="List roles in the community",
)
async def list_roles(community: CommunityById) -> Sequence[Role]:
    return await Role.find_all_by_kwargs(community_id=community.id)


@router.get(
    "/roles/{role_id}/",
    response_model=Role.ListPermissionsSchema,
    summary="Retrieve any role by id",
)
async def retrieve_role(role: RoleById) -> Role:
    return role


class UpdatePermissionsSchema(Role.PatchSchema):
    permissions: list[Permission] | None


@router.patch(
    "/roles/{role_id}/",
    response_model=Role.ListPermissionsSchema,
    summary="Update any role by id",
)
async def patch_role(
    role: RoleById,
    role_data: UpdatePermissionsSchema,
) -> Role:
    role.update(
        **role_data.model_dump(
            exclude={
                "permissions",
            }
        )
    )
    if role_data.permissions:
        role.permissions.clear()
        role.permissions.extend(
            [
                RolePermission(role_id=role.id, permission=permission)
                for permission in role_data.permissions
            ]
        )
    return role


@router.delete(
    "/roles/{role_id}/",
    status_code=204,
    summary="Delete any role by id",
)
async def delete_role(role: RoleById) -> None:
    await role.delete()
