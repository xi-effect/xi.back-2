from typing import Annotated
from uuid import UUID

from fastapi import Depends, Path
from starlette import status

from app.common.fastapi_ext import Responses, with_responses
from app.scheduler.models.event_instances_db import AnyEventInstance, EventInstance
from app.scheduler.models.events_db import ClassroomEvent


class EventInstanceResponses(Responses):
    EVENT_INSTANCE_NOT_FOUND = status.HTTP_404_NOT_FOUND, "Event instance not found"


@with_responses(EventInstanceResponses)
async def get_event_instance_by_id(
    event_instance_id: Annotated[UUID, Path()],
) -> AnyEventInstance:
    event_instance = await EventInstance.find_first_by_id(event_instance_id)
    if event_instance is None:
        raise EventInstanceResponses.EVENT_INSTANCE_NOT_FOUND
    if not isinstance(event_instance, AnyEventInstance):  # pragma: no cover
        raise TypeError("SQLAlchemy returned an unknown type of EventInstance")
    return event_instance


EventInstanceByID = Annotated[AnyEventInstance, Depends(get_event_instance_by_id)]


class ClassroomEventInstanceResponses(Responses):
    EVENT_INSTANCE_IS_NOT_IN_A_CLASSROOM = (
        status.HTTP_403_FORBIDDEN,
        "Event instance is not in a classroom",
    )


@with_responses(ClassroomEventInstanceResponses)
async def get_classroom_event_by_instance_id(
    event_instance: EventInstanceByID,
) -> ClassroomEvent:
    if not isinstance(event_instance.event, ClassroomEvent):
        raise ClassroomEventInstanceResponses.EVENT_INSTANCE_IS_NOT_IN_A_CLASSROOM
    return event_instance.event


ClassroomEventByInstanceID = Annotated[
    ClassroomEvent,
    Depends(get_classroom_event_by_instance_id),
]


class MyClassroomEventInstanceResponses(Responses):
    CLASSROOM_EVENT_INSTANCE_ACCESS_DENIED = (
        status.HTTP_403_FORBIDDEN,
        "Classroom event instance access denied",
    )


@with_responses(MyClassroomEventInstanceResponses)
async def get_my_classroom_event_instance_by_ids(
    event_instance: EventInstanceByID,
    classroom_event: ClassroomEventByInstanceID,
    classroom_id: Annotated[int, Path()],
) -> AnyEventInstance:
    if classroom_event.classroom_id != classroom_id:
        raise MyClassroomEventInstanceResponses.CLASSROOM_EVENT_INSTANCE_ACCESS_DENIED
    return event_instance


MyClassroomEventInstanceByIDs = Annotated[
    AnyEventInstance,
    Depends(get_my_classroom_event_instance_by_ids),
]


EventInstanceIndex = Annotated[int, Path(ge=0)]
