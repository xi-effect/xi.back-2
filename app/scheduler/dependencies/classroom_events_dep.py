from typing import Annotated

from fastapi import Depends, Path
from starlette import status

from app.common.fastapi_ext import Responses, with_responses
from app.scheduler.models.events_db import ClassroomEvent


class ClassroomEventResponses(Responses):
    CLASSROOM_EVENT_NOT_FOUND = status.HTTP_404_NOT_FOUND, "Classroom event not found"


@with_responses(ClassroomEventResponses)
async def get_classroom_event_by_id(event_id: Annotated[int, Path()]) -> ClassroomEvent:
    classroom_event = await ClassroomEvent.find_first_by_id(event_id)
    if classroom_event is None:
        raise ClassroomEventResponses.CLASSROOM_EVENT_NOT_FOUND
    return classroom_event


ClassroomEventByID = Annotated[ClassroomEvent, Depends(get_classroom_event_by_id)]


class MyClassroomEventResponses(Responses):
    CLASSROOM_EVENT_ACCESS_DENIED = (
        status.HTTP_403_FORBIDDEN,
        "Classroom event access denied",
    )


@with_responses(MyClassroomEventResponses)
async def get_my_classroom_event_by_ids(
    classroom_event: ClassroomEventByID,
    classroom_id: Annotated[int, Path()],
) -> ClassroomEvent:
    if classroom_event.classroom_id != classroom_id:
        raise MyClassroomEventResponses.CLASSROOM_EVENT_ACCESS_DENIED
    return classroom_event


MyClassroomEventByIDs = Annotated[
    ClassroomEvent, Depends(get_my_classroom_event_by_ids)
]
