from datetime import datetime
from os import stat
from typing import Any

from starlette.responses import FileResponse, Response
from starlette.staticfiles import NotModifiedResponse

from app.content.models.files_db import File


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
