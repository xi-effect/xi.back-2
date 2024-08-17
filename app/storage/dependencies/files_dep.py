from typing import Annotated
from uuid import UUID

from fastapi import Depends, Path

from app.common.fastapi_ext import Responses, with_responses
from app.storage.models.files_db import File


class FileResponses(Responses):
    FILE_NOT_FOUND = 404, "File not found"


@with_responses(FileResponses)
async def get_file_by_id(file_id: Annotated[UUID, Path()]) -> File:
    file = await File.find_first_by_id(file_id)
    if file is None:
        raise FileResponses.FILE_NOT_FOUND
    return file


FileByIdDependency = Depends(get_file_by_id)
FileById = Annotated[File, FileByIdDependency]