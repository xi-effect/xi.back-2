from typing import Annotated

from fastapi import Path
from pydantic import BaseModel
from starlette import status

from app.common.fastapi_ext import APIRouterExt
from app.scheduler.dependencies.classroom_events_dep import MyClassroomEventByIDs
from app.scheduler.models.events_db import ClassroomEvent
from app.scheduler.models.occurrence_modes_db import OccurrenceModeInputSchema

router = APIRouterExt(tags=["tutor classroom events"])


class ClassroomEventInputSchema(BaseModel):
    event: ClassroomEvent.InputSchema
    occurrence_mode: OccurrenceModeInputSchema


@router.post(
    path="/roles/tutor/classrooms/{classroom_id}/events/",
    status_code=status.HTTP_201_CREATED,
    response_model=ClassroomEvent.ResponseSchema,
    summary="Create a new event in a classroom by id",
)
async def create_classroom_event(
    classroom_id: Annotated[int, Path()],
    data: ClassroomEventInputSchema,
) -> ClassroomEvent:
    event = await ClassroomEvent.create(
        **data.event.model_dump(),
        classroom_id=classroom_id,
    )
    await data.occurrence_mode.db_class.create(
        **data.occurrence_mode.model_dump(),
        event_id=event.id,
    )
    return event


@router.patch(
    path="/roles/tutor/classrooms/{classroom_id}/events/{event_id}/",
    response_model=ClassroomEvent.ResponseSchema,
    summary="Update a classroom event by ids",
)
async def patch_classroom_event(
    classroom_event: MyClassroomEventByIDs,
    data: ClassroomEvent.PatchSchema,
) -> ClassroomEvent:
    classroom_event.update(**data.model_dump(exclude_defaults=True))
    return classroom_event


@router.delete(
    path="/roles/tutor/classrooms/{classroom_id}/events/{event_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a classroom event by ids",
)
async def delete_classroom_event(classroom_event: MyClassroomEventByIDs) -> None:
    await classroom_event.delete()
