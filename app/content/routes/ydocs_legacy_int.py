from typing import Annotated

from fastapi import Depends, Header, Response
from starlette import status

from app.common.config import content_token_provider
from app.common.dependencies.api_key_dep import APIKeyProtection
from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt, with_responses
from app.common.schemas.content_sch import ContentTokenPayloadSchema, YDocAccessLevel
from app.content.dependencies.content_token_dep import ContentTokenResponses
from app.content.dependencies.ydocs_dep import YDocByID, YDocContent
from app.content.models.materials_db import Material
from app.content.models.ydocs_db import YDoc

# TODO (218) legacy mount of the ydoc routes for xi.hocus, remove after it's repointed
router = APIRouterExt(
    dependencies=[APIKeyProtection],
    include_in_schema=False,
    prefix="/internal/storage-service/v2",
    tags=["ydocs internal (legacy)"],
)


@with_responses(ContentTokenResponses)
def validate_and_deserialize_content_token(
    x_storage_token: Annotated[str, Header()],
    auth_data: AuthorizationData,
) -> ContentTokenPayloadSchema:
    content_token_payload = content_token_provider.validate_and_deserialize(
        token=x_storage_token
    )
    if content_token_payload is None:
        raise ContentTokenResponses.INVALID_CONTENT_TOKEN

    if (
        content_token_payload.user_id is not None
        and auth_data.user_id != content_token_payload.user_id
    ):
        raise ContentTokenResponses.INVALID_CONTENT_TOKEN

    return content_token_payload


@with_responses(ContentTokenResponses)
async def get_my_ydoc_by_id(
    ydoc: YDocByID,
    content_token_payload: Annotated[
        ContentTokenPayloadSchema,
        Depends(validate_and_deserialize_content_token),
    ],
) -> YDoc:
    if content_token_payload.ydoc_id != ydoc.id:
        raise ContentTokenResponses.INVALID_CONTENT_TOKEN
    return ydoc


@router.get(
    "/ydocs/{ydoc_id}/access-level/",
    deprecated=True,
    summary="Retrieve user's access level to a ydoc",
)
async def retrieve_ydoc_access_level(
    content_token_payload: Annotated[
        ContentTokenPayloadSchema,
        Depends(validate_and_deserialize_content_token),
    ],
    _ydoc: Annotated[YDoc, Depends(get_my_ydoc_by_id)],
) -> YDocAccessLevel:
    return content_token_payload.ydoc_access_level


@router.get(
    "/ydocs/{ydoc_id}/content/",
    deprecated=True,
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
    deprecated=True,
    summary="Update ydoc's content",
)
async def update_ydoc_content(ydoc: YDocByID, content: YDocContent) -> None:
    await Material.update_main_ydoc_content(main_ydoc_id=ydoc.id, content=content)


@router.delete(
    "/ydocs/{ydoc_id}/content/",
    status_code=status.HTTP_204_NO_CONTENT,
    deprecated=True,
    summary="Clear ydoc's content",
)
async def clear_ydoc_content(ydoc: YDocByID) -> None:
    await Material.update_main_ydoc_content(main_ydoc_id=ydoc.id, content=None)
