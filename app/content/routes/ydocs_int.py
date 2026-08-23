from fastapi import Response
from starlette import status

from app.common.fastapi_ext import APIRouterExt
from app.common.schemas.content_sch import YDocAccessLevel
from app.content.dependencies.content_token_dep import ContentTokenPayload
from app.content.dependencies.ydocs_dep import MyYDocByID, YDocByID, YDocContent
from app.content.models.materials_db import Material

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


@router.get(
    "/ydocs/{ydoc_id}/content/",
    summary="Retrieve ydoc's content",
)
async def retrieve_ydoc_content(ydoc: YDocByID) -> Response:
    return Response(
        content=await ydoc.awaitable_attrs.content,
        media_type="application/octet-stream",
    )


@router.put(
    "/ydocs/{ydoc_id}/content/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Update ydoc's content",
)
async def update_ydoc_content(ydoc: YDocByID, content: YDocContent) -> None:
    await Material.update_main_ydoc_content(main_ydoc_id=ydoc.id, content=content)


@router.delete(
    "/ydocs/{ydoc_id}/content/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Clear ydoc's content",
)
async def clear_ydoc_content(ydoc: YDocByID) -> None:
    await Material.update_main_ydoc_content(main_ydoc_id=ydoc.id, content=None)
