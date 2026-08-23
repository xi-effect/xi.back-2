from collections.abc import Sequence

from starlette import status
from starlette.responses import Response

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt
from app.content.dependencies.files_dep import (
    IfModifiedSinceHeader,
    IfNoneMatchHeader,
    MyLibraryFileByID,
)
from app.content.models.files_db import File, FileSearchRequestSchema
from app.content.services import files_svc

router = APIRouterExt(tags=["library files"])


@router.post(
    path="/roles/tutor/files/searches/",
    response_model=list[File.LibraryResponseSchema],
    summary="List paginated library files for the current user",
)
async def list_library_files(
    auth_data: AuthorizationData,
    data: FileSearchRequestSchema,
) -> Sequence[File]:
    return await File.find_paginated_by_owner_id(
        owner_id=auth_data.user_id,
        search_params=data,
    )


@router.get(
    path="/roles/tutor/files/{file_id}/meta/",
    response_model=File.LibraryResponseSchema,
    summary="Retrieve meta of a library file by id",
)
async def retrieve_library_file_meta(file: MyLibraryFileByID) -> File:
    return file


@router.get(
    path="/roles/tutor/files/{file_id}/",
    response_model=File.LibraryResponseSchema,
    summary="Retrieve a library file by id",
)
async def retrieve_library_file(
    file: MyLibraryFileByID,
    if_none_match: IfNoneMatchHeader = "",
    if_modified_since: IfModifiedSinceHeader = None,
) -> Response:
    return files_svc.build_file_response(
        file=file,
        if_none_match=if_none_match,
        if_modified_since=if_modified_since,
    )


@router.delete(
    path="/roles/tutor/files/{file_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a library file by id",
)
async def delete_library_file(file: MyLibraryFileByID) -> None:
    await file.delete()
