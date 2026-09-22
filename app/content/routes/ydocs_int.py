from starlette import status

from app.common.fastapi_ext import APIRouterExt
from app.common.schemas.content_sch import YDocAccessLevel
from app.content.dependencies.content_token_dep import ContentTokenPayload
from app.content.dependencies.ydocs_dep import MyYDocByID, YDocByID
from app.content.models.materials_db import Material
from app.content.models.ydocs_db import YDoc

router = APIRouterExt(tags=["ydocs internal"])


@router.get(
    "/ydocs/{ydoc_id}/access-level/",
    summary="Retrieve user's access level to a ydoc",
)
async def retrieve_ydoc_access_level(
    content_token_payload: ContentTokenPayload,
    _ydoc: MyYDocByID,
) -> YDocAccessLevel:
    return content_token_payload.ydoc_access_level


@router.put(
    "/ydocs/{ydoc_id}/content-meta/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Update ydoc's content's meta",
)
async def update_ydoc_content_meta(
    ydoc: YDocByID,
    input_data: YDoc.ContentMetaInputSchema,
) -> None:
    await Material.update_main_ydoc_content_meta(
        main_ydoc_id=ydoc.id,
        size_bytes=input_data.size_bytes,
    )
