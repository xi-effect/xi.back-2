from starlette import status

from app.classrooms.dependencies.classroom_notes_dep import ClassroomNoteByID
from app.classrooms.dependencies.classrooms_tutor_dep import (
    MyTutorClassroomByID,
)
from app.classrooms.models.classroom_notes_db import ClassroomNote
from app.common.config import storage_token_provider
from app.common.config_bdg import storage_v2_bridge
from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt, Responses
from app.common.schemas.storage_sch import (
    StorageTokenPayloadSchema,
    StorageYDocItemSchema,
    YDocAccessLevel,
)

router = APIRouterExt(tags=["tutor classroom notes"])


def generate_storage_item_data_from_classroom_note(
    classroom_note: ClassroomNote, auth_data: AuthorizationData
) -> StorageYDocItemSchema:
    return StorageYDocItemSchema(
        access_group_id=classroom_note.access_group_id,
        ydoc_id=classroom_note.ydoc_id,
        storage_token=storage_token_provider.serialize_and_sign(
            StorageTokenPayloadSchema(
                access_group_id=classroom_note.access_group_id,
                user_id=auth_data.user_id,
                can_upload_files=True,
                can_read_files=True,
                ydoc_access_level=YDocAccessLevel.READ_WRITE,
            )
        ),
    )


class ExistingClassroomNoteResponses(Responses):
    CLASSROOM_NOTE_ALREADY_EXISTS = (
        status.HTTP_409_CONFLICT,
        "Classroom note already exists",
    )


@router.post(
    path="/roles/tutor/classrooms/{classroom_id}/note/storage-item/",
    status_code=status.HTTP_201_CREATED,
    responses=ExistingClassroomNoteResponses.responses(),
    summary="Create a tutor classroom note for a classroom by id",
)
async def create_classroom_note(
    classroom: MyTutorClassroomByID,
    auth_data: AuthorizationData,
) -> StorageYDocItemSchema:
    if await ClassroomNote.find_first_by_id(classroom.id) is not None:
        raise ExistingClassroomNoteResponses.CLASSROOM_NOTE_ALREADY_EXISTS

    access_group_data = await storage_v2_bridge.create_access_group()

    classroom_note = await ClassroomNote.create(
        classroom_id=classroom.id,
        access_group_id=access_group_data.id,
        ydoc_id=access_group_data.main_ydoc_id,
    )
    return generate_storage_item_data_from_classroom_note(
        classroom_note=classroom_note,
        auth_data=auth_data,
    )


@router.get(
    path="/roles/tutor/classrooms/{classroom_id}/note/storage-item/",
    summary="Retrieve a storage item of a tutor classroom note for a classroom by id",
)
async def retrieve_classroom_note_storage_item(
    _classroom: MyTutorClassroomByID,
    classroom_note: ClassroomNoteByID,
    auth_data: AuthorizationData,
) -> StorageYDocItemSchema:
    return generate_storage_item_data_from_classroom_note(
        classroom_note=classroom_note,
        auth_data=auth_data,
    )
