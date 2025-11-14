from typing import Annotated
from uuid import UUID

from fastapi import Depends, Path
from starlette import status

from app.common.fastapi_ext import Responses, with_responses
from app.storage_v2.dependencies.storage_token_dep import (
    StorageTokenPayload,
    StorageTokenResponses,
)
from app.storage_v2.models.access_groups_db import AccessGroupFile
from app.storage_v2.models.files_db import File


class FileResponses(Responses):
    FILE_NOT_FOUND = status.HTTP_404_NOT_FOUND, "File not found"


@with_responses(FileResponses)
async def get_file_by_id(file_id: Annotated[UUID, Path()]) -> File:
    file = await File.find_first_by_id(file_id)
    if file is None:
        raise FileResponses.FILE_NOT_FOUND
    return file


FileByID = Annotated[File, Depends(get_file_by_id)]


@with_responses(StorageTokenResponses)
async def get_my_file_by_id(
    file: FileByID,
    storage_token_payload: StorageTokenPayload,
) -> File:
    access_group_file = await AccessGroupFile.find_first_by_ids(
        access_group_id=storage_token_payload.access_group_id,
        file_id=file.id,
    )
    if access_group_file is None:
        raise StorageTokenResponses.INVALID_STORAGE_TOKEN

    return file


MyFileByID = Annotated[File, Depends(get_my_file_by_id)]
