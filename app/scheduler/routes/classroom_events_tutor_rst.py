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
from app.scheduler.models.repetition_modes_db import (
    RepetitionModeInputSchema,
    RepetitionModeResponseSchema,
    REPETITION_MODE_TYPE_ADAPTER,
)

router = APIRouterExt(tags=["tutor classroom events"])


class EventSchemaKind(StrEnum):
    SINGLE = auto()
    REPEATING = auto()


class BaseEventInputSchema(BaseModel):
    event: ClassroomEvent.InputSchema


class SingleEventInputSchema(BaseEventInputSchema):
    kind: Literal[EventSchemaKind.SINGLE] = EventSchemaKind.SINGLE
    sole_instance: SoleEventInstanceInputSchema


class RepeatingEventInputSchema(BaseEventInputSchema):
    kind: Literal[EventSchemaKind.REPEATING] = EventSchemaKind.REPEATING
    repetition_mode: RepetitionModeInputSchema


EventInputSchema = Annotated[
    SingleEventInputSchema | RepeatingEventInputSchema,
    Field(discriminator="kind"),
]


class BaseEventResponseSchema(BaseModel):
    event: ClassroomEvent.ResponseSchema


class SingleEventResponseSchema(BaseEventResponseSchema):
    kind: Literal[EventSchemaKind.SINGLE] = EventSchemaKind.SINGLE
    sole_instance: SoleEventInstance.StandaloneResponseSchema


class RepeatingEventResponseSchema(BaseEventResponseSchema):
    kind: Literal[EventSchemaKind.REPEATING] = EventSchemaKind.REPEATING
    repetition_mode: RepetitionModeResponseSchema


EventResponseSchema = Annotated[
    SingleEventResponseSchema | RepeatingEventResponseSchema,
    Field(discriminator="kind"),
]


@router.post(
    path="/roles/tutor/classrooms/{classroom_id}/events/",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new event in a classroom by id",
)
async def create_classroom_event(
    classroom_id: Annotated[int, Path()],
    data: EventInputSchema,
) -> EventResponseSchema:
    classroom_event = await ClassroomEvent.create(
        **data.event.model_dump(),
        classroom_id=classroom_id,
    )

    match data:
        case SingleEventInputSchema():
            sole_instance = await SoleEventInstance.create(
                **data.sole_instance.model_dump(),
                event_id=classroom_event.id,
            )
            return SingleEventResponseSchema(
                event=ClassroomEvent.ResponseSchema.model_validate(
                    classroom_event, from_attributes=True
                ),
                sole_instance=SoleEventInstance.StandaloneResponseSchema.model_validate(
                    sole_instance,
                    from_attributes=True,
                ),
            )
        case RepeatingEventInputSchema():
            repetition_mode = await data.repetition_mode.db_class.create(
                **data.repetition_mode.model_dump(),
                event_id=classroom_event.id,
            )
            return RepeatingEventResponseSchema(
                event=ClassroomEvent.ResponseSchema.model_validate(
                    classroom_event, from_attributes=True
                ),
                repetition_mode=REPETITION_MODE_TYPE_ADAPTER.validate_python(
                    repetition_mode,
                    from_attributes=True,
                ),
            )
        case _:
            assert_never(data)


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
