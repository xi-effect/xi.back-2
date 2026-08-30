from datetime import datetime
from io import BytesIO
from os import stat
from pathlib import Path
from typing import Any

from fastapi import UploadFile
from PIL import Image
from starlette.responses import FileResponse, Response
from starlette.staticfiles import NotModifiedResponse

from app.content.models.files_db import File, FileKind


def convert_image_content_to_webp(image_content: bytes) -> bytes:
    image = Image.open(BytesIO(image_content))
    converted_image_buffer = BytesIO()
    image.save(converted_image_buffer, format="webp")
    converted_image_buffer.seek(0)
    return converted_image_buffer.read()


DEFAULT_CONTENT_TYPE = "application/octet-stream"

WEBP_CONTENT_TYPE = "image/webp"


async def create_file_from_upload(
    upload: UploadFile,
    file_kind: FileKind,
    owner_id: int,
    uploader_id: int,
) -> File:
    if file_kind is FileKind.IMAGE:
        upload_content = convert_image_content_to_webp(await upload.read())
        content_type = WEBP_CONTENT_TYPE
    else:
        upload_content = await upload.read()
        content_type = upload.content_type or DEFAULT_CONTENT_TYPE

    filename = Path(upload.filename or "upload")

    return await File.create_with_content(
        content=upload_content,
        owner_id=owner_id,
        uploader_id=uploader_id,
        name=filename.stem,
        extension=filename.suffix.lstrip("."),
        file_kind=file_kind,
        content_type=content_type,
    )


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
