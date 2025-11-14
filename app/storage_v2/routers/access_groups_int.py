from starlette import status

from app.common.fastapi_ext import APIRouterExt
from app.storage_v2.dependencies.access_groups_dep import AccessGroupByID
from app.storage_v2.models.access_groups_db import AccessGroup, AccessGroupFile
from app.storage_v2.models.ydocs_db import YDoc

router = APIRouterExt(tags=["access groups internal"])


@router.post(
    "/access-groups/",
    status_code=status.HTTP_201_CREATED,
    response_model=AccessGroup.ResponseSchema,
    summary="Create a new access group",
)
async def create_access_group() -> AccessGroup:
    main_ydoc = await YDoc.create()
    return await AccessGroup.create(main_ydoc_id=main_ydoc.id)


@router.post(
    "/access-groups/{access_group_id}/duplicates/",
    status_code=status.HTTP_201_CREATED,
    response_model=AccessGroup.ResponseSchema,
    summary="Duplicate an access group by id",
)
async def duplicate_access_group(source_access_group: AccessGroupByID) -> AccessGroup:
    new_main_ydoc_id = await YDoc.duplicate_by_id(source_access_group.main_ydoc_id)

    new_access_group = await AccessGroup.create(main_ydoc_id=new_main_ydoc_id)

    await AccessGroupFile.duplicate_all_links_by_access_group(
        source_access_group_id=source_access_group.id,
        target_access_group_id=new_access_group.id,
    )

    return new_access_group


@router.delete(
    "/access-groups/{access_group_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete any access group by id",
)
async def delete_access_group(access_group: AccessGroupByID) -> None:
    await access_group.delete()
