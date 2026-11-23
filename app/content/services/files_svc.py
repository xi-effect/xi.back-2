from collections.abc import AsyncIterator
from datetime import datetime
from io import BytesIO
from os import stat
from pathlib import Path
from typing import Any, cast

from fastapi import UploadFile
from PIL import Image
from starlette.responses import FileResponse, Response
from starlette.staticfiles import NotModifiedResponse

from app.common.schemas.content_sch import FileKind
from app.content.models.files_db import File
from app.content.models.ydocs_db import CONTENT_COPY_CHUNK_SIZE, write_file_from_chunks
from app.content.services import storage_svc


def convert_image_content_to_webp(image_content: bytes) -> bytes:
    image = Image.open(BytesIO(image_content))
    converted_image_buffer = BytesIO()
    image.save(converted_image_buffer, format="webp")
    converted_image_buffer.seek(0)
    return converted_image_buffer.read()


DEFAULT_CONTENT_TYPE = "application/octet-stream"

WEBP_CONTENT_TYPE = "image/webp"
WEBP_EXTENSION = "webp"


async def read_upload_in_chunks(upload: UploadFile) -> AsyncIterator[bytes]:
    while True:
        chunk = await upload.read(CONTENT_COPY_CHUNK_SIZE)
        if len(chunk) == 0:
            break
        yield chunk


async def yield_single_chunk(chunk: bytes) -> AsyncIterator[bytes]:
    yield chunk


async def create_file_from_upload(
    upload: UploadFile,
    file_kind: FileKind,
    owner_id: int,
    uploader_id: int,
) -> File:
    upload_size = cast(int, upload.size)
    await storage_svc.ensure_owner_can_store_file(
        owner_id=owner_id,
        file_kind=file_kind,
        size_bytes=upload_size,
    )

    filename = Path(upload.filename or "upload")

    if file_kind is FileKind.IMAGE:
        image_content = convert_image_content_to_webp(await upload.read())
        size_bytes = len(image_content)
        chunks = yield_single_chunk(image_content)
        content_type = WEBP_CONTENT_TYPE
        extension = WEBP_EXTENSION
    else:
        size_bytes = upload_size
        chunks = read_upload_in_chunks(upload)
        content_type = upload.content_type or DEFAULT_CONTENT_TYPE
        extension = filename.suffix.lstrip(".")

    file = await File.create(
        owner_id=owner_id,
        uploader_id=uploader_id,
        name=filename.stem,
        extension=extension,
        kind=file_kind,
        content_type=content_type,
        size_bytes=size_bytes,
        file_tags=[],
    )
    file.path.parent.mkdir(parents=True, exist_ok=True)
    await write_file_from_chunks(path=file.path, chunks=chunks)
    return file


def parse_http_datetime(value: str) -> datetime:
    return datetime.strptime(value, "%a, %d %b %Y %H:%M:%S GMT")


def parse_http_datetime_header(value: Any) -> Any:
    return parse_http_datetime(value) if isinstance(value, str) else value


def build_file_response(
    file: File,
    if_none_match: str,
    if_modified_since: datetime | None,
) -> Response:
    response = FileResponse(
        path=file.path,
        filename=file.filename,
        media_type=file.content_type,
        content_disposition_type=file.content_disposition,
        stat_result=stat(file.path),
    )

    etag = response.headers.get("etag")
    if etag in {tag.strip(" W/") for tag in if_none_match.split(",")}:
        return NotModifiedResponse(headers=response.headers)

    last_modified = parse_http_datetime(response.headers["last-modified"])
    if if_modified_since is not None and if_modified_since >= last_modified:
        return NotModifiedResponse(headers=response.headers)

    return response
