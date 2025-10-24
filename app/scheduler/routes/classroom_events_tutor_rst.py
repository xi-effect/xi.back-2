from collections.abc import Sequence
from typing import Annotated, Self

from fastapi import Path
from pydantic import model_validator
from starlette import status

from app.common.fastapi_ext import APIRouterExt
from app.scheduler.dependencies.classroom_events_dep import (
    MyClassroomEventByIDs,
)
from app.scheduler.dependencies.events_dep import EventTimeFrameQuery
from app.scheduler.models.events_db import ClassroomEvent

router = APIRouterExt(tags=["tutor classroom events"])


@router.get(
    path="/roles/tutor/classrooms/{classroom_id}/events/",
    response_model=list[ClassroomEvent.ResponseSchema],
    summary="List paginated events in a classroom by id",
)
async def list_classroom_events(
    classroom_id: Annotated[int, Path()],
    time_frame: EventTimeFrameQuery,
) -> Sequence[ClassroomEvent]:
    return await ClassroomEvent.find_all_by_classroom_id_in_time_frame(
        classroom_id=classroom_id,
        happens_after=time_frame.happens_after,
        happens_before=time_frame.happens_before,
    )


class ClassroomEventInputSchema(ClassroomEvent.InputSchema):
    @model_validator(mode="after")
    def validate_event_start_and_end_time(self) -> Self:
        if self.starts_at >= self.ends_at:
            raise ValueError(
                "the start time of an event cannot be greater than or equal to the end time"
            )
        return self


@router.post(
    path="/roles/tutor/classrooms/{classroom_id}/events/",
    status_code=status.HTTP_201_CREATED,
    response_model=ClassroomEvent.ResponseSchema,
    summary="Create a new event in a classroom by id",
)
async def create_classroom_event(
    classroom_id: Annotated[int, Path()],
    input_data: ClassroomEventInputSchema,
) -> ClassroomEvent:
    return await ClassroomEvent.create(
        **input_data.model_dump(), classroom_id=classroom_id
    )


@router.get(
    path="/roles/tutor/classrooms/{classroom_id}/events/{event_id}/",
    response_model=ClassroomEvent.ResponseSchema,
    summary="Retrieve a classroom event by ids",
)
async def retrieve_classroom_event(
    classroom_event: MyClassroomEventByIDs,
) -> ClassroomEvent:
    return classroom_event


@router.put(
    path="/roles/tutor/classrooms/{classroom_id}/events/{event_id}/",
    response_model=ClassroomEvent.ResponseSchema,
    summary="Update a classroom event by ids",
)
async def put_classroom_event(
    classroom_event: MyClassroomEventByIDs,
    put_data: ClassroomEventInputSchema,
) -> ClassroomEvent:
    classroom_event.update(**put_data.model_dump())
    return classroom_event


@router.delete(
    path="/roles/tutor/classrooms/{classroom_id}/events/{event_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a classroom event by ids",
)
async def delete_classroom_event(classroom_event: MyClassroomEventByIDs) -> None:
    await classroom_event.delete()
