from fastapi import Depends, UploadFile
from starlette import status
from starlette.responses import Response

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt
from app.content.dependencies.content_token_dep import (
    ensure_content_token_allows_reading_files,
    ensure_content_token_allows_uploading_files,
)
from app.content.dependencies.files_dep import (
    IfModifiedSinceHeader,
    IfNoneMatchHeader,
    MyFileByID,
)
from app.content.dependencies.uploads_dep import UploadFileKind
from app.content.dependencies.ydocs_dep import ContentTokenYDoc
from app.content.models.files_db import File
from app.content.models.ydoc_files_db import YDocFile
from app.content.services import files_svc

router = APIRouterExt(tags=["files"])


@router.post(
    "/files/",
    status_code=status.HTTP_201_CREATED,
    response_model=File.ResponseSchema,
    summary="Upload a new file",
    dependencies=[Depends(ensure_content_token_allows_uploading_files)],
)
async def upload_file(
    ydoc: ContentTokenYDoc,
    auth_data: AuthorizationData,
    upload: UploadFile,
    file_kind: UploadFileKind,
) -> File:
    file = await files_svc.create_file_from_upload(
        upload=upload,
        file_kind=file_kind,
        owner_id=ydoc.owner_id,
        uploader_id=auth_data.user_id,
    )

    await YDocFile.create(
        ydoc_id=ydoc.id,
        file_id=file.id,
    )

    return file


@router.get(
    "/files/{file_id}/meta/",
    response_model=File.ResponseSchema,
    summary="Retrieve meta of any file by id",
    dependencies=[Depends(ensure_content_token_allows_reading_files)],
)
async def retrieve_file_meta(file: MyFileByID) -> File:
    return file


@router.get(
    "/files/{file_id}/",
    response_model=File.ResponseSchema,
    summary="Retrieve any file by id",
    dependencies=[Depends(ensure_content_token_allows_reading_files)],
)
async def retrieve_file(
    file: MyFileByID,
    if_none_match: IfNoneMatchHeader = "",
    if_modified_since: IfModifiedSinceHeader = None,
) -> Response:
    return files_svc.build_file_response(
        file=file,
        if_none_match=if_none_match,
        if_modified_since=if_modified_since,
    )
