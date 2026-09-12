import zlib
from collections.abc import AsyncIterator
from typing import Annotated, Final

from fastapi import Header, Request
from starlette import status
from starlette.responses import FileResponse, Response

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


YDOC_CONTENT_MEDIA_TYPE: Final[str] = "application/octet-stream"


@router.get(
    "/ydocs/{ydoc_id}/content/",
    summary="Retrieve ydoc's content",
)
async def retrieve_ydoc_content(ydoc: YDocByID) -> Response:
    if not ydoc.path.exists():
        return Response(media_type=YDOC_CONTENT_MEDIA_TYPE)
    return FileResponse(
        path=ydoc.path,
        media_type=YDOC_CONTENT_MEDIA_TYPE,
        headers={"Content-Encoding": "gzip"},
    )


GZIP_WBITS: Final[int] = 16 + zlib.MAX_WBITS


class RawContentCompressor:  # TODO remove once xi.hocus sends gzipped content
    def __init__(self, raw_content_stream: AsyncIterator[bytes]) -> None:
        self.raw_content_stream = raw_content_stream
        self.size_bytes = 0

    async def __aiter__(self) -> AsyncIterator[bytes]:
        compressor = zlib.compressobj(wbits=GZIP_WBITS)
        async for chunk in self.raw_content_stream:
            self.size_bytes += len(chunk)
            yield compressor.compress(chunk)
        yield compressor.flush()


@router.put(
    "/ydocs/{ydoc_id}/content/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Update ydoc's content",
)
async def update_ydoc_content(
    ydoc: YDocByID,
    request: Request,
    x_size_bytes: Annotated[int | None, Header()] = None,
) -> None:
    if x_size_bytes is None:  # TODO remove once xi.hocus sends gzipped content
        compressor = RawContentCompressor(request.stream())
        await ydoc.write_content(compressor)
        size_bytes = compressor.size_bytes
    else:
        await ydoc.write_content(request.stream())
        size_bytes = x_size_bytes

    await Material.update_main_ydoc_content_meta(
        main_ydoc_id=ydoc.id,
        size_bytes=size_bytes,
    )


@router.delete(
    "/ydocs/{ydoc_id}/content/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Clear ydoc's content",
)
async def clear_ydoc_content(ydoc: YDocByID) -> None:
    ydoc.delete_content()
    await Material.update_main_ydoc_content_meta(main_ydoc_id=ydoc.id, size_bytes=0)


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
