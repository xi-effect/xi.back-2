from typing import Annotated

from fastapi import Depends, Path
from starlette import status

from app.common.fastapi_ext import Responses, with_responses
from app.content.models.materials_db import ClassroomNoteMaterial


class ClassroomNoteResponses(Responses):
    CLASSROOM_NOTE_NOT_FOUND = status.HTTP_404_NOT_FOUND, "Classroom note not found"


@with_responses(ClassroomNoteResponses)
async def get_classroom_note_material_by_classroom_id(
    classroom_id: Annotated[int, Path()],
) -> ClassroomNoteMaterial:
    classroom_note_material = await ClassroomNoteMaterial.find_first_by_kwargs(
        classroom_id=classroom_id,
    )
    if classroom_note_material is None:
        raise ClassroomNoteResponses.CLASSROOM_NOTE_NOT_FOUND
    return classroom_note_material


ClassroomNoteMaterialByClassroomID = Annotated[
    ClassroomNoteMaterial,
    Depends(get_classroom_note_material_by_classroom_id),
]
