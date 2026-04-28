from enum import StrEnum, auto
from typing import Annotated, Literal, assert_never

from fastapi import Path
from pydantic import BaseModel, Field
from starlette import status

from app.common.fastapi_ext import APIRouterExt
from app.scheduler.dependencies.classroom_events_dep import MyClassroomEventByIDs
from app.scheduler.models.event_instances_db import (
    SoleEventInstance,
    SoleEventInstanceInputSchema,
)
from app.scheduler.models.events_db import ClassroomEvent
from app.scheduler.models.repetition_modes_db import RepetitionModeInputSchema

router = APIRouterExt(tags=["tutor classroom events"])


class EventInputKind(StrEnum):
    SINGLE = auto()
    REPEATING = auto()


class BaseEventInputSchema(BaseModel):
    event: ClassroomEvent.InputSchema


class SingleEventInputSchema(BaseEventInputSchema):
    kind: Literal[EventInputKind.SINGLE] = EventInputKind.SINGLE
    sole_instance: SoleEventInstanceInputSchema


class RepeatingEventInputSchema(BaseEventInputSchema):
    kind: Literal[EventInputKind.REPEATING] = EventInputKind.REPEATING
    repetition_mode: RepetitionModeInputSchema


EventInputSchema = Annotated[
    SingleEventInputSchema | RepeatingEventInputSchema,
    Field(discriminator="kind"),
]


@router.post(
    path="/roles/tutor/classrooms/{classroom_id}/events/",
    status_code=status.HTTP_201_CREATED,
    response_model=ClassroomEvent.ResponseSchema,
    summary="Create a new event in a classroom by id",
)
async def create_classroom_event(
    classroom_id: Annotated[int, Path()],
    data: EventInputSchema,
) -> ClassroomEvent:
    event = await ClassroomEvent.create(
        **data.event.model_dump(),
        classroom_id=classroom_id,
    )

    match data:
        case SingleEventInputSchema():
            await SoleEventInstance.create(
                **data.sole_instance.model_dump(),
                event_id=event.id,
            )
        case RepeatingEventInputSchema():
            await data.repetition_mode.db_class.create(
                **data.repetition_mode.model_dump(),
                event_id=event.id,
            )
        case _:
            assert_never(data)

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
