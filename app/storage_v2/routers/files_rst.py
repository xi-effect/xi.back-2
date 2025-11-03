from datetime import datetime
from os import stat
from typing import Annotated

from fastapi import Header, UploadFile
from starlette import status
from starlette.responses import FileResponse, Response
from starlette.staticfiles import NotModifiedResponse

from app.common.fastapi_ext import APIRouterExt
from app.common.schemas.storage_sch import StorageTokenPayloadSchema
from app.storage_v2.dependencies.files_dep import MyFileByID
from app.storage_v2.dependencies.storage_token_dep import (
    StorageTokenPayload,
    StorageTokenResponses,
)
from app.storage_v2.dependencies.uploads_dep import ValidatedImageUpload
from app.storage_v2.models.access_groups_db import AccessGroup, AccessGroupFile
from app.storage_v2.models.files_db import File, FileKind

router = APIRouterExt(tags=["files"])


async def upload_file(
    storage_token_payload: StorageTokenPayloadSchema,
    upload: UploadFile,
    file_kind: FileKind,
) -> File:
    if not storage_token_payload.can_upload_files:
        raise StorageTokenResponses.INVALID_STORAGE_TOKEN

    access_group = await AccessGroup.find_first_by_id(
        storage_token_payload.access_group_id
    )
    if access_group is None:
        raise StorageTokenResponses.INVALID_STORAGE_TOKEN

    file = await File.create_with_content(
        content=upload.file,
        filename=upload.filename,
        file_kind=file_kind,
    )

    await AccessGroupFile.create(
        access_group_id=storage_token_payload.access_group_id,
        file_id=file.id,
    )

    return file


@router.post(
    "/file-kinds/uncategorized/files/",
    status_code=status.HTTP_201_CREATED,
    response_model=File.ResponseSchema,
    summary="Upload a new uncategorized file",
)
async def upload_uncategorized_file(
    storage_token_payload: StorageTokenPayload,
    upload: UploadFile,
) -> File:
    return await upload_file(
        storage_token_payload=storage_token_payload,
        upload=upload,
        file_kind=FileKind.UNCATEGORIZED,
    )


@router.post(
    "/file-kinds/image/files/",
    status_code=status.HTTP_201_CREATED,
    response_model=File.ResponseSchema,
    summary="Upload a new image file",
)
async def upload_image_file(
    storage_token_payload: StorageTokenPayload,
    upload: ValidatedImageUpload,
) -> File:
    return await upload_file(
        storage_token_payload=storage_token_payload,
        upload=upload,
        file_kind=FileKind.IMAGE,
    )


@router.get(
    "/files/{file_id}/meta/",
    response_model=File.ResponseSchema,
    summary="Read meta of any file by id",
)
async def retrieve_file_meta(
    storage_token_payload: StorageTokenPayload,
    file: MyFileByID,
) -> File:
    if not storage_token_payload.can_read_files:
        raise StorageTokenResponses.INVALID_STORAGE_TOKEN
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
    storage_token_payload: StorageTokenPayload,
    file: MyFileByID,
    if_none_match: Annotated[str, Header()] = "",
    if_modified_since: Annotated[str | None, Header()] = None,
) -> Response:
    if not storage_token_payload.can_read_files:
        raise StorageTokenResponses.INVALID_STORAGE_TOKEN

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
