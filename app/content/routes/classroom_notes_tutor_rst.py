from typing import Annotated

from fastapi import Path
from starlette import status

from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt, Responses
from app.common.schemas.content_sch import ContentYDocItemSchema, YDocAccessLevel
from app.content.dependencies.classroom_notes_dep import (
    ClassroomNoteMaterialByClassroomID,
)
from app.content.models.materials_db import ClassroomNoteMaterial
from app.content.models.ydocs_db import YDoc, YDocContentKind
from app.content.services import materials_svc

router = APIRouterExt(tags=["tutor classroom notes"])


class ClassroomNoteConflictResponses(Responses):
    CLASSROOM_NOTE_ALREADY_EXISTS = (
        status.HTTP_409_CONFLICT,
        "Classroom note already exists",
    )


@router.post(
    path="/roles/tutor/classrooms/{classroom_id}/note/storage-item/",
    status_code=status.HTTP_201_CREATED,
    responses=ClassroomNoteConflictResponses.responses(),
    summary="Create a new classroom note for a classroom by id",
)
async def create_classroom_note(
    auth_data: AuthorizationData,
    classroom_id: Annotated[int, Path()],
) -> ContentYDocItemSchema:
    if await ClassroomNoteMaterial.is_present_by_classroom_id(classroom_id):
        raise ClassroomNoteConflictResponses.CLASSROOM_NOTE_ALREADY_EXISTS

    main_ydoc = await YDoc.create(
        owner_id=auth_data.user_id,
        content_kind=YDocContentKind.NOTE,
    )
    classroom_note_material = await ClassroomNoteMaterial.create(
        main_ydoc=main_ydoc,
        classroom_id=classroom_id,
    )
    return materials_svc.build_ydoc_item(
        material=classroom_note_material,
        user_id=auth_data.user_id,
        can_upload_files=True,
        can_add_library_files=True,
        ydoc_access_level=YDocAccessLevel.READ_WRITE,
    )


@router.get(
    path="/roles/tutor/classrooms/{classroom_id}/note/storage-item/",
    summary="Retrieve a storage item of a classroom note for a classroom by id",
)
async def retrieve_classroom_note_storage_item(
    classroom_note_material: ClassroomNoteMaterialByClassroomID,
    auth_data: AuthorizationData,
) -> ContentYDocItemSchema:
    return materials_svc.build_ydoc_item(
        material=classroom_note_material,
        user_id=auth_data.user_id,
        can_upload_files=True,
        can_add_library_files=True,
        ydoc_access_level=YDocAccessLevel.READ_WRITE,
    )
