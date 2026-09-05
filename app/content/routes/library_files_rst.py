from collections.abc import Sequence
from typing import Annotated

from fastapi import Body, UploadFile
from starlette import status
from starlette.responses import Response

from app.common.config_bdg import autocomplete_bridge
from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt, Responses
from app.common.schemas.autocomplete_sch import TagKind
from app.content.dependencies.files_dep import (
    IfModifiedSinceHeader,
    IfNoneMatchHeader,
    MyLibraryFileByID,
)
from app.content.dependencies.uploads_dep import UploadFileKind
from app.content.models.files_db import (
    ClassroomFile,
    File,
    FileSearchRequestSchema,
    FileTag,
)
from app.content.services import files_svc

router = APIRouterExt(tags=["library files"])


@router.post(
    path="/roles/tutor/files/searches/",
    response_model=list[File.TutorResponseSchema],
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


@router.post(
    path="/roles/tutor/files/",
    status_code=status.HTTP_201_CREATED,
    response_model=File.TutorResponseSchema,
    summary="Upload a new library file for the current user",
)
async def upload_library_file(
    auth_data: AuthorizationData,
    upload: UploadFile,
    file_kind: UploadFileKind,
) -> File:
    return await files_svc.create_file_from_upload(
        upload=upload,
        file_kind=file_kind,
        owner_id=auth_data.user_id,
        uploader_id=auth_data.user_id,
    )


@router.get(
    path="/roles/tutor/files/{file_id}/meta/",
    response_model=File.TutorResponseSchema,
    summary="Retrieve meta of a library file by id",
)
async def retrieve_library_file_meta(file: MyLibraryFileByID) -> File:
    return file


@router.get(
    path="/roles/tutor/files/{file_id}/",
    response_model=File.TutorResponseSchema,
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


@router.get(
    path="/roles/tutor/files/{file_id}/classroom-ids/",
    summary="List all classroom ids for a library file by id",
)
async def list_library_file_classroom_ids(file: MyLibraryFileByID) -> Sequence[int]:
    return await ClassroomFile.find_all_classroom_ids_by_file_id(file_id=file.id)


@router.patch(
    path="/roles/tutor/files/{file_id}/",
    response_model=File.TutorResponseSchema,
    summary="Update a library file by id",
)
async def patch_library_file(
    file: MyLibraryFileByID,
    patch_data: File.PatchSchema,
) -> File:
    file.update(**patch_data.model_dump(exclude_defaults=True))
    return file


class TagResponses(Responses):
    TAG_NOT_FOUND = status.HTTP_404_NOT_FOUND, "Tag not found"


@router.put(
    path="/roles/tutor/files/{file_id}/tags/",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=TagResponses.responses(),
    summary="Set tags for a library file by id",
)
async def set_library_file_tags(
    auth_data: AuthorizationData,
    file: MyLibraryFileByID,
    tag_ids: Annotated[
        set[int],
        Body(embed=True, max_length=FileTag.max_count_per_file),
    ],
) -> None:
    if len(tag_ids) != 0:
        tag_id_to_tag = await autocomplete_bridge.retrieve_multiple_tags(
            kind=TagKind.GENERIC,
            tag_ids=list(tag_ids),
            tutor_id=auth_data.user_id,
        )
        if not tag_ids.issubset(tag_id_to_tag.keys()):
            raise TagResponses.TAG_NOT_FOUND
    await FileTag.replace_all_by_file_id(
        file_id=file.id,
        tag_ids=tag_ids,
    )


@router.delete(
    path="/roles/tutor/files/{file_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a library file by id",
)
async def delete_library_file(file: MyLibraryFileByID) -> None:
    await file.delete()
