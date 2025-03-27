from collections.abc import Sequence
from typing import Self

from fastapi import HTTPException
from pydantic import AwareDatetime, model_validator

from app.common.fastapi_ext import APIRouterExt
from app.scheduler.dependencies.events_dep import EventById
from app.scheduler.models.events_db import Event

router = APIRouterExt(tags=["scheduler-events mub"])


class EventInputSchema(Event.InputSchema):
    @model_validator(mode="after")
    def validate_event_start_and_end_time(self) -> Self:
        if self.starts_at >= self.ends_at:
            raise ValueError(
                "the start time of an event cannot be greater than or equal to the end time"
            )
        return self


@router.get(
    path="/events/",
    response_model=list[Event.ResponseSchema],
    summary="List all events",
)
async def list_events(
    happens_after: AwareDatetime, happens_before: AwareDatetime
) -> Sequence[Event]:
    if happens_after >= happens_before:
        raise HTTPException(
            status_code=422,
            detail="Parameter happens_before must be later in time than happens_after",
        )
    return await Event.find_all_events_in_time_frame(
        happens_after=happens_after, happens_before=happens_before
    )


@router.post(
    path="/events/",
    status_code=201,
    response_model=Event.ResponseSchema,
    summary="Create a new event",
)
async def create_event(data: EventInputSchema) -> Event:
    return await Event.create(**data.model_dump())


@router.get(
    path="/events/{event_id}/",
    response_model=Event.ResponseSchema,
    summary="Retrieve any event by id",
)
async def retrieve_event(event: EventById) -> Event:
    return event


@router.put(
    path="/events/{event_id}/",
    response_model=Event.ResponseSchema,
    summary="Update any event by id",
)
async def put_event(
    event: EventById,
    data: EventInputSchema,
) -> Event:
    event.update(**data.model_dump())
    return event


@router.delete(
    path="/events/{event_id}/", status_code=204, summary="Delete any event by id"
)
async def delete_event(event: EventById) -> None:
    await event.delete()
