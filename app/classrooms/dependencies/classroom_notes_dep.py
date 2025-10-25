from typing import Annotated

from fastapi import Depends, Path
from starlette import status

from app.classrooms.models.classroom_notes_db import ClassroomNote
from app.common.fastapi_ext import Responses, with_responses


class ClassroomNoteResponses(Responses):
    CLASSROOM_NOTE_NOT_FOUND = status.HTTP_404_NOT_FOUND, "Classroom note not found"


@with_responses(ClassroomNoteResponses)
async def get_classroom_note_by_id(
    classroom_id: Annotated[int, Path()],
) -> ClassroomNote:
    classroom_note = await ClassroomNote.find_first_by_id(classroom_id)
    if classroom_note is None:
        raise ClassroomNoteResponses.CLASSROOM_NOTE_NOT_FOUND
    return classroom_note


ClassroomNoteByID = Annotated[ClassroomNote, Depends(get_classroom_note_by_id)]
