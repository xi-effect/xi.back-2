from typing import Annotated

from fastapi import Depends, Path
from starlette import status

from app.common.fastapi_ext import Responses, with_responses
from app.content.dependencies.files_dep import FileByID
from app.content.models.files_db import ClassroomFile


class ClassroomFileResponses(Responses):
    CLASSROOM_FILE_NOT_FOUND = status.HTTP_404_NOT_FOUND, "Classroom file not found"


@with_responses(ClassroomFileResponses)
async def get_classroom_file_by_ids(
    file: FileByID,
    classroom_id: Annotated[int, Path()],
) -> ClassroomFile:
    classroom_file = await ClassroomFile.find_first_by_ids(
        file_id=file.id,
        classroom_id=classroom_id,
    )
    if classroom_file is None:
        raise ClassroomFileResponses.CLASSROOM_FILE_NOT_FOUND
    return classroom_file


ClassroomFileByIDs = Annotated[ClassroomFile, Depends(get_classroom_file_by_ids)]
