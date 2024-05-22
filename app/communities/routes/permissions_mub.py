from collections.abc import Sequence

from app.common.fastapi_ext import APIRouterExt, Responses
from app.communities.dependencies.roles_dep import RoleById
from app.communities.models.permissions_db import Permission, RolePermission

router = APIRouterExt(tags=["permissions meta mub"])


class AddPermissionResponses(Responses):
    PERMISSION_ADDED = 409, "Permission is already added"


@router.post(
    "/roles/{role_id}/permissions/{permission}/",
    status_code=201,
    response_model=RolePermission.FullResponseSchema,
    responses=AddPermissionResponses.responses(),
    summary="Add permission for the role",
)
async def add_permission(role: RoleById, permission: Permission) -> RolePermission:
    role_permission = await RolePermission.find_first_by_kwargs(
        role_id=role.id, permission=permission
    )
    if role_permission is not None:
        raise AddPermissionResponses.PERMISSION_ADDED
    return await RolePermission.create(role_id=role.id, permission=permission)


@router.get(
    "/roles/{role_id}/permissions/",
    response_model=list[RolePermission.FullResponseSchema],
    summary="List permissions of the role",
)
async def list_permissions(role: RoleById) -> Sequence[RolePermission]:
    return await RolePermission.find_all_by_kwargs(role_id=role.id)


class RemovePermissionResponses(Responses):
    MISSING_PERMISSION = 404, "Role has no this permission"


@router.delete(
    "/roles/{role_id}/permissions/{permission}/",
    status_code=204,
    responses=RemovePermissionResponses.responses(),
    summary="Remove any role permission by id",
)
async def remove_permission(role: RoleById, permission: Permission) -> None:
    role_permission = await RolePermission.find_first_by_kwargs(
        role_id=role.id, permission=permission
    )
    if role_permission is None:
        raise RemovePermissionResponses.MISSING_PERMISSION
    await role_permission.delete()
