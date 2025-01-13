from datetime import datetime
from os import stat
from typing import Annotated

from fastapi import Header, UploadFile
from starlette.responses import FileResponse, Response
from starlette.staticfiles import NotModifiedResponse

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt
from app.storage.dependencies.access_groups_dep import AccessGroupById
from app.storage.dependencies.files_dep import FileById
from app.storage.dependencies.uploads_dep import ValidatedImageUpload
from app.storage.models.files_db import File, FileKind

router = APIRouterExt(tags=["files"])


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
    return await File.create_with_content(
        content=upload.file,
        filename=upload.filename,
        file_kind=FileKind.UNCATEGORIZED,
        creator_user_id=auth_data.user_id,
    )


@router.post(
    "/access-groups/{access_group_id}/file-kinds/uncategorized/files/",
    status_code=201,
    response_model=File.ResponseSchema,
    summary="Upload a new uncategorized file to an access group",
)
async def upload_private_uncategorized_file(
    auth_data: AuthorizationData,
    access_group: AccessGroupById,
    upload: UploadFile,
) -> File:
    # TODO check if allowed to upload (41239612 / 44012321)
    return await File.create_with_content(
        content=upload.file,
        filename=upload.filename,
        file_kind=FileKind.UNCATEGORIZED,
        creator_user_id=auth_data.user_id,
        access_group_id=access_group.id,
    )


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
    summary="Upload a new public image file",
)
async def upload_public_image_file(
    auth_data: AuthorizationData,
    upload: ValidatedImageUpload,
) -> File:
    return await File.create_with_content(
        content=upload.file,
        filename=upload.filename,
        file_kind=FileKind.IMAGE,
        creator_user_id=auth_data.user_id,
    )


@router.post(
    "/access-groups/{access_group_id}/file-kinds/image/files/",
    status_code=201,
    response_model=File.ResponseSchema,
    summary="Upload a new image file to an access group",
)
async def upload_private_image_file(
    auth_data: AuthorizationData,
    access_group: AccessGroupById,
    upload: ValidatedImageUpload,
) -> File:
    # TODO check if allowed to upload (41239612 / 44012321)
    return await File.create_with_content(
        content=upload.file,
        filename=upload.filename,
        file_kind=FileKind.IMAGE,
        creator_user_id=auth_data.user_id,
        access_group_id=access_group.id,
    )


@router.get(
    "/files/{file_id}/meta/",
    response_model=File.ResponseSchema,
    summary="Read meta of any file by id",
)
async def retrieve_file_meta(file: FileById) -> File:
    # TODO check access to file (41239612 / 44012321)
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
    # TODO check access to file (41239612 / 44012321)

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
    # TODO check access to file or disable method(?) (41239612 / 44012321)
    await file.delete()
