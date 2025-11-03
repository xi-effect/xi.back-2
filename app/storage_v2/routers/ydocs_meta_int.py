from starlette import status

from app.common.fastapi_ext import APIRouterExt
from app.storage_v2.dependencies.access_groups_dep import AccessGroupByID
from app.storage_v2.models.access_groups_db import AccessGroupYDoc
from app.storage_v2.models.ydocs_db import YDoc

router = APIRouterExt(tags=["ydocs meta internal"])


@router.post(
    "/access-groups/{access_group_id}/ydocs/",
    status_code=status.HTTP_201_CREATED,
    response_model=YDoc.ResponseSchema,
    summary="Create a new ydoc",
)
async def create_ydoc(access_group: AccessGroupByID) -> YDoc:
    ydoc = await YDoc.create()
    await AccessGroupYDoc.create(
        access_group_id=access_group.id,
        ydoc_id=ydoc.id,
    )
    return ydoc
