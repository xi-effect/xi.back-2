from collections.abc import Sequence
from typing import Annotated

from fastapi import Path

from app.common.fastapi_ext import APIRouterExt
from app.scheduler.dependencies.classroom_events_dep import (
    MyClassroomEventByIDs,
)
from app.scheduler.dependencies.events_dep import EventTimeFrameQuery
from app.scheduler.models.events_db import ClassroomEvent

router = APIRouterExt(tags=["student classroom events"])


@router.get(
    path="/roles/student/classrooms/{classroom_id}/events/",
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


@router.get(
    path="/roles/student/classrooms/{classroom_id}/events/{event_id}/",
    response_model=ClassroomEvent.ResponseSchema,
    summary="Retrieve a classroom event by ids",
)
async def retrieve_classroom_event(
    classroom_event: MyClassroomEventByIDs,
) -> ClassroomEvent:
    return classroom_event
