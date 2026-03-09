from typing import Annotated, Self

from fastapi import Depends, Path, Query
from pydantic import AwareDatetime, BaseModel, model_validator
from starlette import status

from app.common.fastapi_ext import Responses, with_responses
from app.scheduler.models.events_db import ClassroomEvent, Event


class EventTimeFrameSchema(BaseModel):
    happens_after: AwareDatetime
    happens_before: AwareDatetime

    @model_validator(mode="after")
    def validate_happens_after_and_happens_before(self) -> Self:
        if self.happens_after >= self.happens_before:
            raise ValueError(
                "parameter happens_before must be later in time than happens_after"
            )
        return self


EventTimeFrameQuery = Annotated[EventTimeFrameSchema, Query()]


class EventResponses(Responses):
    EVENT_NOT_FOUND = status.HTTP_404_NOT_FOUND, "Event not found"


AnyEvent = ClassroomEvent


@with_responses(EventResponses)
async def get_event_by_id(event_id: Annotated[int, Path()]) -> AnyEvent:
    event = await Event.find_first_by_id(event_id)
    if event is None:
        raise EventResponses.EVENT_NOT_FOUND
    if not isinstance(event, AnyEvent):  # pragma: no cover
        raise TypeError("SQLAlchemy returned an unknown type of Classroom")
    return event


EventByID = Annotated[AnyEvent, Depends(get_event_by_id)]
