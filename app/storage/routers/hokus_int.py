from fastapi import Response

from app.common.fastapi_ext import APIRouterExt
from app.storage.dependencies.access_groups_dep import AccessGroupById
from app.storage.dependencies.hokus_dep import HokuById, HokuContent
from app.storage.models.hokus_db import Hoku

router = APIRouterExt(tags=["hokus internal"])


@router.post(
    "/access-groups/{access_group_id}/hokus/",
    status_code=201,
    response_model=Hoku.ResponseSchema,
    summary="Create a new hoku",
)
async def create_hoku(access_group: AccessGroupById) -> Hoku:
    return await Hoku.create(access_group_id=access_group.id)


@router.get(
    "/hokus/{hoku_id}/content/",
    summary="Retrieve hoku's content",
)
async def retrieve_hoku_content(hoku: HokuById) -> Response:
    return Response(content=hoku.content, media_type="application/octet-stream")


@router.put(
    "/hokus/{hoku_id}/content/",
    status_code=204,
    summary="Update hoku's content",
)
async def update_hoku_content(hoku: HokuById, content: HokuContent) -> None:
    hoku.update(content=content)


@router.delete(
    "/hokus/{hoku_id}/content/",
    status_code=204,
    summary="Clear hoku's content",
)
async def clear_hoku_content(hoku: HokuById) -> None:
    hoku.update(content=None)
