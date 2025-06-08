from typing import assert_never

from fastapi import Response
from starlette import status

from app.common.config_bdg import communities_bridge
from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt
from app.common.schemas.storage_sch import StorageAccessGroupKind, YDocAccessLevel
from app.storage.dependencies.access_groups_dep import AccessGroupById
from app.storage.dependencies.ydocs_dep import YDocById, YDocContent
from app.storage.models.access_groups_db import AccessGroup
from app.storage.models.ydocs_db import YDoc

router = APIRouterExt(tags=["ydocs internal"])


@router.post(
    "/access-groups/{access_group_id}/ydocs/",
    status_code=status.HTTP_201_CREATED,
    response_model=YDoc.ResponseSchema,
    summary="Create a new ydoc",
)
async def create_ydoc(access_group: AccessGroupById) -> YDoc:
    return await YDoc.create(access_group_id=access_group.id)


@router.get(
    "/ydocs/{ydoc_id}/access-level/",
    summary="Retrieve user's access level to a ydoc",
)
async def retrieve_ydoc_access_level(
    auth_data: AuthorizationData,
    ydoc: YDocById,
) -> YDocAccessLevel:
    access_group: AccessGroup = await ydoc.awaitable_attrs.access_group

    match access_group.kind:
        case StorageAccessGroupKind.BOARD_CHANNEL:
            return await communities_bridge.retrieve_board_channel_access_level(
                board_channel_id=access_group.related_id,
                auth_data=auth_data,
            )
        case _:  # pragma: no cover  # typing only
            assert_never(access_group.kind)


@router.get(
    "/ydocs/{ydoc_id}/content/",
    summary="Retrieve ydoc's content",
)
async def retrieve_ydoc_content(ydoc: YDocById) -> Response:
    return Response(content=ydoc.content, media_type="application/octet-stream")


@router.put(
    "/ydocs/{ydoc_id}/content/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Update ydoc's content",
)
async def update_ydoc_content(ydoc: YDocById, content: YDocContent) -> None:
    ydoc.update(content=content)


@router.delete(
    "/ydocs/{ydoc_id}/content/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Clear ydoc's content",
)
async def clear_ydoc_content(ydoc: YDocById) -> None:
    ydoc.update(content=None)
