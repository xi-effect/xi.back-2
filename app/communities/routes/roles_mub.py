from collections.abc import Sequence

from app.common.fastapi_ext import APIRouterExt
from app.communities.dependencies.communities_dep import CommunityById
from app.communities.dependencies.roles_dep import RoleById
from app.communities.models.roles_db import Role

router = APIRouterExt(tags=["roles meta mub"])


@router.post(
    "/communities/{community_id}/roles/",
    status_code=201,
    response_model=Role.FullResponseSchema,
    summary="Create a new role in the community",
)
async def create_role(community: CommunityById, data: Role.FullInputSchema) -> Role:
    return await Role.create(
        community_id=community.id,
        **data.model_dump(exclude_defaults=True),
    )


@router.get(
    "/communities/{community_id}/roles/",
    response_model=list[Role.FullResponseSchema],
    summary="List roles in the community",
)
async def list_roles(community: CommunityById) -> Sequence[Role]:
    return await Role.find_all_by_kwargs(community_id=community.id)


@router.get(
    "/roles/{role_id}/",
    response_model=Role.FullResponseSchema,
    summary="Retrieve any role by id",
)
async def retrieve_role(role: RoleById) -> Role:
    return role


@router.patch(
    "/roles/{role_id}/",
    response_model=Role.FullResponseSchema,
    summary="Update any role by id",
)
async def patch_role(role: RoleById, data: Role.FullPatchSchema) -> Role:
    role.update(**data.model_dump(exclude_defaults=True))
    return role


@router.delete(
    "/roles/{role_id}/",
    status_code=204,
    summary="Delete any role by id",
)
async def delete_role(role: RoleById) -> None:
    await role.delete()
