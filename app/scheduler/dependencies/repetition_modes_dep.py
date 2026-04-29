from typing import Annotated
from uuid import UUID

from fastapi import Depends, Path
from starlette import status

from app.common.fastapi_ext import Responses, with_responses
from app.scheduler.models.events_db import ClassroomEvent
from app.scheduler.models.repetition_modes_db import RepetitionMode


class RepetitionModeResponses(Responses):
    REPETITION_MODE_NOT_FOUND = status.HTTP_404_NOT_FOUND, "Repetition mode not found"


@with_responses(RepetitionModeResponses)
async def get_repetition_mode_by_id(
    repetition_mode_id: Annotated[UUID, Path()],
) -> RepetitionMode:
    repetition_mode = await RepetitionMode.find_first_by_id(repetition_mode_id)
    if repetition_mode is None:
        raise RepetitionModeResponses.REPETITION_MODE_NOT_FOUND
    return repetition_mode


RepetitionModeByID = Annotated[RepetitionMode, Depends(get_repetition_mode_by_id)]


class ClassroomRepetitionModeResponses(Responses):
    REPETITION_MODE_IS_NOT_IN_A_CLASSROOM = (
        status.HTTP_403_FORBIDDEN,
        "Repetition mode is not in a classroom",
    )


@with_responses(ClassroomRepetitionModeResponses)
async def get_classroom_event_by_repetition_mode_id(
    repetition_mode: RepetitionModeByID,
) -> ClassroomEvent:
    if not isinstance(repetition_mode.event, ClassroomEvent):
        raise ClassroomRepetitionModeResponses.REPETITION_MODE_IS_NOT_IN_A_CLASSROOM
    return repetition_mode.event


ClassroomEventByRepetitionModeID = Annotated[
    ClassroomEvent,
    Depends(get_classroom_event_by_repetition_mode_id),
]


class MyClassroomRepetitionModeResponses(Responses):
    CLASSROOM_REPETITION_MODE_ACCESS_DENIED = (
        status.HTTP_403_FORBIDDEN,
        "Classroom repetition mode access denied",
    )


@with_responses(MyClassroomRepetitionModeResponses)
async def get_my_classroom_repetition_mode_by_ids(
    repetition_mode: RepetitionModeByID,
    classroom_event: ClassroomEventByRepetitionModeID,
    classroom_id: Annotated[int, Path()],
) -> RepetitionMode:
    if classroom_event.classroom_id != classroom_id:
        raise MyClassroomRepetitionModeResponses.CLASSROOM_REPETITION_MODE_ACCESS_DENIED
    return repetition_mode


MyClassroomRepetitionModeByIDs = Annotated[
    RepetitionMode,
    Depends(get_my_classroom_repetition_mode_by_ids),
]
