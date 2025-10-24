from collections.abc import Sequence
from typing import Annotated

from fastapi import Path, Query

from app.common.fastapi_ext import APIRouterExt
from app.scheduler.dependencies.classroom_events_dep import MyClassroomEventByIDs
from app.scheduler.models.events_db import ClassroomEvent
from app.scheduler.routes.classroom_events_tutor_rst import ClassroomEventSearchParams

router = APIRouterExt(tags=["Student classroom events"])


@router.get(
    path="/roles/student/classrooms/{classroom_id}/events/",
    response_model=list[ClassroomEvent.ResponseSchema],
    summary="List paginated events in a classroom by id",
)
async def list_classroom_events(
    classroom_id: Annotated[int, Path()],
    search_params: Annotated[ClassroomEventSearchParams, Query()],
) -> Sequence[ClassroomEvent]:
    return await ClassroomEvent.find_all_by_classroom_id_in_time_frame(
        classroom_id=classroom_id,
        happens_after=search_params.happens_after,
        happens_before=search_params.happens_before,
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
