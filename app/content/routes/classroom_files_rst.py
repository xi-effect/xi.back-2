from collections.abc import Sequence
from typing import Annotated

from fastapi import Depends, Path, UploadFile
from starlette import status
from starlette.responses import Response

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt
from app.content.dependencies.classroom_files_dep import (
    ClassroomFileByIDs,
    get_classroom_file_by_ids,
)
from app.content.dependencies.files_dep import (
    FileByID,
    IfModifiedSinceHeader,
    IfNoneMatchHeader,
    MyLibraryFileByID,
)
from app.content.dependencies.uploads_dep import UploadFileKind
from app.content.models.files_db import ClassroomFile, File, FileSearchRequestSchema
from app.content.services import files_svc

router = APIRouterExt(tags=["classroom files"])


@router.post(
    path="/roles/tutor/classrooms/{classroom_id}/files/searches/",
    response_model=list[File.TutorResponseSchema],
    summary="List paginated files in a classroom by id",
)
@router.post(
    path="/roles/student/classrooms/{classroom_id}/files/searches/",
    response_model=list[File.StudentResponseSchema],
    summary="List paginated files in a classroom by id",
)
async def list_classroom_files(
    classroom_id: Annotated[int, Path()],
    data: FileSearchRequestSchema,
) -> Sequence[File]:
    return await File.find_paginated_by_classroom_id(
        classroom_id=classroom_id,
        search_params=data,
    )


@router.post(
    path="/roles/tutor/classrooms/{classroom_id}/files/",
    status_code=status.HTTP_201_CREATED,
    response_model=File.TutorResponseSchema,
    summary="Upload a new file to a classroom by id",
)
async def upload_file_to_classroom(
    auth_data: AuthorizationData,
    classroom_id: Annotated[int, Path()],
    upload: UploadFile,
    file_kind: UploadFileKind,
) -> File:
    file = await files_svc.create_file_from_upload(
        upload=upload,
        file_kind=file_kind,
        owner_id=auth_data.user_id,
        uploader_id=auth_data.user_id,
    )
    await ClassroomFile.create(file_id=file.id, classroom_id=classroom_id)
    return file


@router.put(
    path="/roles/tutor/classrooms/{classroom_id}/files/{file_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Add a library file to a classroom by ids",
)
async def add_library_file_to_classroom(
    classroom_id: Annotated[int, Path()],
    file: MyLibraryFileByID,
) -> None:
    await ClassroomFile.upsert_by_ids(file_id=file.id, classroom_id=classroom_id)


@router.get(
    path="/roles/tutor/classrooms/{classroom_id}/files/{file_id}/meta/",
    response_model=File.TutorResponseSchema,
    summary="Retrieve meta of a classroom file by ids",
    dependencies=[Depends(get_classroom_file_by_ids)],
)
@router.get(
    path="/roles/student/classrooms/{classroom_id}/files/{file_id}/meta/",
    response_model=File.StudentResponseSchema,
    summary="Retrieve meta of a classroom file by ids",
    dependencies=[Depends(get_classroom_file_by_ids)],
)
async def retrieve_classroom_file_meta(file: FileByID) -> File:
    return file


@router.get(
    path="/roles/tutor/classrooms/{classroom_id}/files/{file_id}/",
    response_model=File.TutorResponseSchema,
    summary="Retrieve a classroom file by ids",
    dependencies=[Depends(get_classroom_file_by_ids)],
)
@router.get(
    path="/roles/student/classrooms/{classroom_id}/files/{file_id}/",
    response_model=File.StudentResponseSchema,
    summary="Retrieve a classroom file by ids",
    dependencies=[Depends(get_classroom_file_by_ids)],
)
async def retrieve_classroom_file(
    file: FileByID,
    if_none_match: IfNoneMatchHeader = "",
    if_modified_since: IfModifiedSinceHeader = None,
) -> Response:
    return files_svc.build_file_response(
        file=file,
        if_none_match=if_none_match,
        if_modified_since=if_modified_since,
    )


@router.delete(
    path="/roles/tutor/classrooms/{classroom_id}/files/{file_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a file from a classroom by ids",
)
async def remove_file_from_classroom(classroom_file: ClassroomFileByIDs) -> None:
    await classroom_file.delete()
