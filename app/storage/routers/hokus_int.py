from typing import assert_never

from fastapi import Response

from app.common.access import AccessGroupKind, AccessLevel
from app.common.config_bdg import communities_bridge
from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt
from app.storage.dependencies.access_groups_dep import AccessGroupById
from app.storage.dependencies.hokus_dep import HokuById, HokuContent
from app.storage.models.access_groups_db import AccessGroup
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
    "/hokus/{hoku_id}/access-level/",
    summary="Retrieve user's access level to a hoku",
)
async def retrieve_hoku_access_level(
    auth_data: AuthorizationData,
    hoku: HokuById,
) -> AccessLevel:
    access_group: AccessGroup = await hoku.awaitable_attrs.access_group

    match access_group.kind:
        case AccessGroupKind.BOARD_CHANNEL:
            return await communities_bridge.retrieve_board_channel_access_level(
                board_channel_id=access_group.related_id,
                auth_data=auth_data,
            )
        case _:  # pragma: no cover  # typing only
            assert_never(access_group.kind)


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
