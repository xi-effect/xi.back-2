from datetime import datetime
from os import stat
from shutil import copyfileobj
from typing import Annotated

from fastapi import Header, UploadFile
from filetype import filetype  # type: ignore[import-untyped]
from filetype.types.image import Webp  # type: ignore[import-untyped]
from starlette.responses import FileResponse, Response
from starlette.staticfiles import NotModifiedResponse

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt, Responses
from app.storage.dependencies.files_dep import FileById
from app.storage.models.files_db import File, FileKind

router = APIRouterExt(tags=["files"])


# TODO check access rights for reading and deleting


@router.post(  # TODO remove in 41239612
    "/files/attachments/",
    status_code=201,
    response_model=File.ResponseSchema,
    summary="Use POST /access-groups/public/file-kinds/uncategorized/files/ instead",
    deprecated=True,
)
@router.post(
    "/access-groups/public/file-kinds/uncategorized/files/",
    status_code=201,
    response_model=File.ResponseSchema,
    summary="Upload a new public uncategorized file",
)
async def upload_public_uncategorized_file(
    auth_data: AuthorizationData,
    upload: UploadFile,
) -> File:
    file = await File.create(
        name=upload.filename,
        kind=FileKind.UNCATEGORIZED,
        creator_user_id=auth_data.user_id,
    )
    with file.path.open("wb") as f:
        copyfileobj(upload.file, f)
    return file


class ImageFormatResponses(Responses):
    WRONG_FORMAT = (415, "Invalid image format")


@router.post(  # TODO remove in 41239612
    "/files/images/",
    status_code=201,
    response_model=File.ResponseSchema,
    summary="Use POST /access-groups/public/file-kinds/image/files/ instead",
    deprecated=True,
)
@router.post(
    "/access-groups/public/file-kinds/image/files/",
    status_code=201,
    response_model=File.ResponseSchema,
    responses=ImageFormatResponses.responses(),
    summary="Upload a new public image file",
)
async def upload_public_image_file(
    auth_data: AuthorizationData,
    upload: UploadFile,
) -> File:
    if not filetype.match(upload.file, [Webp()]):
        raise ImageFormatResponses.WRONG_FORMAT

    file = await File.create(
        name=upload.filename,
        kind=FileKind.IMAGE,
        creator_user_id=auth_data.user_id,
    )
    with file.path.open("wb") as f:
        copyfileobj(upload.file, f)  # TODO may be convert to async
    return file


@router.get(
    "/files/{file_id}/meta/",
    response_model=File.ResponseSchema,
    summary="Read meta of any file by id",
)
async def retrieve_file_meta(file: FileById) -> File:
    return file


def parse_http_datetime(header: str | None) -> datetime | None:
    if header is None:
        return None
    return datetime.strptime(header, "%a, %d %b %Y %H:%M:%S GMT")


@router.get(
    "/files/{file_id}/",
    response_model=File.ResponseSchema,
    summary="Read any file by id",
)
async def read_file(
    file: FileById,
    if_none_match: Annotated[str, Header()] = "",
    if_modified_since: Annotated[str | None, Header()] = None,
) -> Response:
    response = FileResponse(
        path=file.path,
        filename=file.name,
        media_type=file.media_type,
        content_disposition_type=file.content_disposition,
        stat_result=stat(file.path),
    )

    etag = response.headers.get("etag")
    if etag in {tag.strip(" W/") for tag in if_none_match.split(",")}:
        return NotModifiedResponse(headers=response.headers)

    modified_since = parse_http_datetime(if_modified_since)
    last_modified = parse_http_datetime(response.headers.get("last-modified"))
    if (
        modified_since is not None
        and last_modified is not None
        and modified_since >= last_modified
    ):
        return NotModifiedResponse(headers=response.headers)

    return response


@router.delete(
    "/files/{file_id}/",
    status_code=204,
    summary="Delete any file by id",
)
async def delete_file(file: FileById) -> None:
    await file.delete()
