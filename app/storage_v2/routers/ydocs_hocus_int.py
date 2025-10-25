from fastapi import Response
from starlette import status

from app.common.fastapi_ext import APIRouterExt
from app.common.schemas.storage_sch import YDocAccessLevel
from app.storage_v2.dependencies.storage_token_dep import StorageTokenPayload
from app.storage_v2.dependencies.ydocs_dep import MyYDocByID, YDocByID, YDocContent

router = APIRouterExt(tags=["ydocs hocus internal"])


@router.get(
    "/ydocs/{ydoc_id}/access-level/",
    summary="Retrieve user's access level to a ydoc",
)
async def retrieve_ydoc_access_level(
    storage_token_payload: StorageTokenPayload,
    _ydoc: MyYDocByID,
) -> YDocAccessLevel:
    return storage_token_payload.ydoc_access_level


@router.get(
    "/ydocs/{ydoc_id}/content/",
    summary="Retrieve ydoc's content",
)
async def retrieve_ydoc_content(ydoc: YDocByID) -> Response:
    return Response(content=ydoc.content, media_type="application/octet-stream")


@router.put(
    "/ydocs/{ydoc_id}/content/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Update ydoc's content",
)
async def update_ydoc_content(ydoc: YDocByID, content: YDocContent) -> None:
    ydoc.update(content=content)


@router.delete(
    "/ydocs/{ydoc_id}/content/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Clear ydoc's content",
)
async def clear_ydoc_content(ydoc: YDocByID) -> None:
    ydoc.update(content=None)
