from starlette import status

from app.common.fastapi_ext import APIRouterExt
from app.storage_v2.dependencies.access_groups_dep import AccessGroupByID
from app.storage_v2.models.access_groups_db import AccessGroup

router = APIRouterExt(tags=["access groups internal"])


@router.post(
    "/access-groups/",
    status_code=status.HTTP_201_CREATED,
    response_model=AccessGroup.ResponseSchema,
    summary="Create a new access group",
)
async def create_access_group() -> AccessGroup:
    return await AccessGroup.create()


@router.delete(
    "/access-groups/{access_group_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete any access group by id",
)
async def delete_access_group(access_group: AccessGroupByID) -> None:
    await access_group.delete()
