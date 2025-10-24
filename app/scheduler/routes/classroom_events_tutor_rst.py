from collections.abc import Sequence

from pydantic import AwareDatetime
from starlette import status

from app.common.fastapi_ext import APIRouterExt, Responses
from app.scheduler.dependencies.classroom_events_dep import MyClassroomEventByIDs
from app.scheduler.models.events_db import ClassroomEvent, EventTimeFrameMixin

router = APIRouterExt(tags=["Tutor classroom events"])


class HappensTimeFrameResponses(Responses):
    INVALID_TIME_FRAME = (
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        "Parameter happens_before must be later in time than happens_after",
    )


@router.get(
    path="/roles/tutor/classrooms/{classroom_id}/events/",
    response_model=list[ClassroomEvent.ResponseSchema],
    responses=HappensTimeFrameResponses.responses(),
    summary="List paginated events in a classroom by id",
)
async def list_classroom_events(
    classroom_id: int, happens_after: AwareDatetime, happens_before: AwareDatetime
) -> Sequence[ClassroomEvent]:
    if happens_after >= happens_before:
        raise HappensTimeFrameResponses.INVALID_TIME_FRAME
    return await ClassroomEvent.find_all_by_classroom_id_in_time_frame(
        classroom_id=classroom_id,
        happens_after=happens_after,
        happens_before=happens_before,
    )


class ClassroomEventInputSchema(EventTimeFrameMixin, ClassroomEvent.InputSchema):
    pass


@router.post(
    path="/roles/tutor/classrooms/{classroom_id}/events/",
    status_code=status.HTTP_201_CREATED,
    response_model=ClassroomEvent.ResponseSchema,
    summary="Create a new event in a classroom by id",
)
async def create_classroom_event(
    input_data: ClassroomEventInputSchema,
    classroom_id: int,
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
