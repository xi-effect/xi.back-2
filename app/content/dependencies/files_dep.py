from typing import Annotated
from uuid import UUID

from fastapi import Depends, Path
from starlette import status

from app.common.fastapi_ext import Responses, with_responses
from app.content.dependencies.content_token_dep import (
    ContentTokenPayload,
    ContentTokenResponses,
)
from app.content.models.files_db import File
from app.content.models.ydoc_files_db import YDocFile


class FileResponses(Responses):
    FILE_NOT_FOUND = status.HTTP_404_NOT_FOUND, "File not found"


@with_responses(FileResponses)
async def get_file_by_id(file_id: Annotated[UUID, Path()]) -> File:
    file = await File.find_first_by_id(file_id)
    if file is None:
        raise FileResponses.FILE_NOT_FOUND
    return file


FileByID = Annotated[File, Depends(get_file_by_id)]


@with_responses(ContentTokenResponses)
async def get_my_file_by_id(
    file: FileByID,
    content_token_payload: ContentTokenPayload,
) -> File:
    ydoc_file = await YDocFile.find_first_by_ids(
        ydoc_id=content_token_payload.ydoc_id,
        file_id=file.id,
    )
    if ydoc_file is None:
        raise ContentTokenResponses.INVALID_CONTENT_TOKEN

    return file


MyFileByID = Annotated[File, Depends(get_my_file_by_id)]
