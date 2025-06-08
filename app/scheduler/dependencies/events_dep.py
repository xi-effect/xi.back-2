from typing import Annotated

from fastapi import Depends, Path
from starlette import status

from app.common.fastapi_ext import Responses, with_responses
from app.scheduler.models.events_db import Event


class EventResponses(Responses):
    EVENT_NOT_FOUND = status.HTTP_404_NOT_FOUND, "Event not found"


@with_responses(EventResponses)
async def get_event_by_id(event_id: Annotated[int, Path()]) -> Event:
    event = await Event.find_first_by_id(event_id)
    if event is None:
        raise EventResponses.EVENT_NOT_FOUND
    return event


EventById = Annotated[Event, Depends(get_event_by_id)]
