from collections.abc import Sequence
from typing import Annotated, assert_never

from fastapi import Path
from pydantic import BaseModel, Field
from pydantic_marshals.base import CompositeMarshalModel
from starlette import status

from app.common.fastapi_ext import APIRouterExt
from app.scheduler.dependencies.classroom_events_dep import (
    MyClassroomEventByIDs,
)
from app.scheduler.dependencies.events_dep import EventTimeFrameQuery
from app.scheduler.models.event_schedules_db import (
    EventScheduleKind,
    EventSchedulesInputSchema,
    OnceEventSchedule,
    WeeklyEventSchedule,
)
from app.scheduler.models.events_db import ClassroomEvent

router = APIRouterExt(tags=["tutor classroom events"])


class ClassroomEventResponseSchema(CompositeMarshalModel):
    classroom_event: Annotated[ClassroomEvent, ClassroomEvent.ResponseSchema]
    schedules: list[
        Annotated[
            Annotated[OnceEventSchedule, OnceEventSchedule.ResponseSchema]
            | Annotated[WeeklyEventSchedule, WeeklyEventSchedule.ResponseSchema],
        ],
        Field(discriminator="kind"),
    ]


@router.get(
    path="/roles/tutor/classrooms/{classroom_id}/events/",
    response_model=list[ClassroomEventResponseSchema],
    summary="List paginated events in a classroom by id",
)
async def list_classroom_events(
    classroom_id: Annotated[int, Path()],
    time_frame: EventTimeFrameQuery,
) -> Sequence[ClassroomEventResponseSchema]:
    classroom_events = await ClassroomEvent.find_all_by_classroom_id_in_time_frame(
        classroom_id=classroom_id,
        happens_after=time_frame.happens_after,
        happens_before=time_frame.happens_before,
    )
    return [
        ClassroomEventResponseSchema(
            classroom_event=classroom_event,
            schedules=await classroom_event.awaitable_attrs.schedules,
        )
        for classroom_event in classroom_events
    ]


class ClassroomEventInputSchema(BaseModel):
    classroom_event: ClassroomEvent.InputSchema
    schedule: EventSchedulesInputSchema


@router.post(
    path="/roles/tutor/classrooms/{classroom_id}/events/",
    status_code=status.HTTP_201_CREATED,
    response_model=ClassroomEventResponseSchema.build_marshal(),
    summary="Create a new event in a classroom by id",
)
async def create_classroom_event(
    classroom_id: Annotated[int, Path()],
    input_data: ClassroomEventInputSchema,
) -> ClassroomEventResponseSchema:
    event = await ClassroomEvent.create(
        **input_data.classroom_event.model_dump(), classroom_id=classroom_id
    )
    match input_data.schedule.kind:
        case EventScheduleKind.ONCE:
            event_schedule = await OnceEventSchedule.create(
                **input_data.schedule.model_dump(), event_id=event.id
            )
        case EventScheduleKind.WEEKLY:
            event_schedule = await WeeklyEventSchedule.create(
                **input_data.schedule.model_dump(), event_id=event.id
            )
        case _:
            assert_never(input_data.schedule.kind)
    return ClassroomEventResponseSchema(
        classroom_event=event, schedules=[event_schedule]
    )


@router.get(
    path="/roles/tutor/classrooms/{classroom_id}/events/{event_id}/",
    response_model=ClassroomEventResponseSchema.build_marshal(),
    summary="Retrieve a classroom event by ids",
)
async def retrieve_classroom_event(
    classroom_event: MyClassroomEventByIDs,
) -> ClassroomEventResponseSchema:
    return ClassroomEventResponseSchema(
        classroom_event=classroom_event,
        schedules=await classroom_event.awaitable_attrs.schedules,
    )


@router.patch(
    path="/roles/tutor/classrooms/{classroom_id}/events/{event_id}/",
    response_model=ClassroomEventResponseSchema.build_marshal(),
    summary="Update a classroom event by ids",
)
async def patch_classroom_event(
    classroom_event: MyClassroomEventByIDs,
    patch_data: ClassroomEvent.PatchSchema,
) -> ClassroomEventResponseSchema:
    classroom_event.update(**patch_data.model_dump(exclude_defaults=True))
    return ClassroomEventResponseSchema(
        classroom_event=classroom_event,
        schedules=await classroom_event.awaitable_attrs.schedules,
    )


@router.delete(
    path="/roles/tutor/classrooms/{classroom_id}/events/{event_id}/",  # fix me
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a classroom event by ids",
)
async def delete_classroom_event(classroom_event: MyClassroomEventByIDs) -> None:
    await classroom_event.delete()
