from datetime import datetime
from enum import StrEnum, auto
from typing import Annotated, Literal, assert_never

from fastapi import Body, Path
from pydantic import AwareDatetime, BaseModel, Field
from starlette import status

from app.common.config_bdg import notifications_bridge
from app.common.fastapi_ext import APIRouterExt
from app.common.schemas.classrooms_sch import ClassroomRole
from app.common.schemas.notifications_sch import (
    ClassroomParticipantRecipientFilterSchema,
    ClassroomScheduleFocusNotificationPayloadSchema,
    NotificationInputV2Schema,
    NotificationKind,
    PersistedClassroomEventInstanceNotificationPayloadSchema,
)
from app.scheduler.dependencies.classroom_events_dep import MyClassroomEventByIDs
from app.scheduler.models.event_instances_db import (
    RepeatedEventInstance,
    SoleEventInstance,
    SoleEventInstanceInputSchema,
)
from app.scheduler.models.events_db import ClassroomEvent
from app.scheduler.models.repetition_modes_db import (
    REPETITION_MODE_TYPE_ADAPTER,
    RepetitionMode,
    RepetitionModeInputSchema,
    RepetitionModeResponseSchema,
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
            await notifications_bridge.send_notification(
                NotificationInputV2Schema(
                    payload=PersistedClassroomEventInstanceNotificationPayloadSchema(
                        kind=NotificationKind.SINGLE_CLASSROOM_EVENT_CREATED_V1,
                        classroom_id=classroom_event.classroom_id,
                        event_instance_id=sole_instance.id,
                    ),
                    recipient_filters=[
                        ClassroomParticipantRecipientFilterSchema(
                            classroom_id=classroom_event.classroom_id,
                            role=ClassroomRole.STUDENT,
                        )
                    ],
                )
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
            repetition_mode: RepetitionMode = (
                await data.repetition_mode.db_class.create(
                    **data.repetition_mode.model_dump(),
                    event_id=classroom_event.id,
                )
            )
            await notifications_bridge.send_notification(
                NotificationInputV2Schema(
                    payload=ClassroomScheduleFocusNotificationPayloadSchema(
                        kind=NotificationKind.REPEATING_CLASSROOM_EVENT_CREATED_V1,
                        classroom_id=classroom_event.classroom_id,
                        focused_at=repetition_mode.starts_at,
                    ),
                    recipient_filters=[
                        ClassroomParticipantRecipientFilterSchema(
                            classroom_id=classroom_event.classroom_id,
                            role=ClassroomRole.STUDENT,
                        )
                    ],
                )
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


async def cancel_repetition_modes_after_timestamp(
    classroom_event: ClassroomEvent,
    timestamp: datetime,
) -> None:
    await RepetitionMode.delete_all_at_or_after_timestamp(
        event_id=classroom_event.id,
        timestamp=timestamp,
    )

    border_repetition_mode = await RepetitionMode.find_last_bordering_on_a_timestamp(
        event_id=classroom_event.id,
        timestamp=timestamp,
    )
    if border_repetition_mode is None:
        return

    last_starts_at = border_repetition_mode.calculate_closest_past_event_instance_starts_at_for_timestamp(
        timestamp=timestamp
    )
    if last_starts_at is None:
        await border_repetition_mode.delete()
        return

    border_repetition_mode.is_finite = True
    border_repetition_mode.ends_at = (
        last_starts_at + border_repetition_mode.event_instance_duration
    )

    last_instance_index: int = (
        border_repetition_mode.calculate_event_instance_index_for_starts_at(
            event_instance_starts_at=last_starts_at
        )
    )
    await RepeatedEventInstance.delete_all_after_index(
        repetition_mode_id=border_repetition_mode.id,
        instance_index=last_instance_index,
    )


@router.post(
    path=(
        "/roles/tutor/classrooms/{classroom_id}"
        "/events/{event_id}/last-repetition-mode/"
    ),
    status_code=status.HTTP_201_CREATED,
    response_model=RepetitionModeResponseSchema,
    summary="Create a new repetition mode at the end for a classroom event by id",
)
async def create_last_repetition_mode(
    classroom_event: MyClassroomEventByIDs,
    data: RepetitionModeInputSchema,
) -> RepetitionMode:
    # TODO (170) check if this is a single event

    await cancel_repetition_modes_after_timestamp(
        classroom_event=classroom_event,
        timestamp=data.starts_at,
    )

    repetition_mode = await data.db_class.create(
        **data.model_dump(),
        event_id=classroom_event.id,
    )

    await notifications_bridge.send_notification(
        NotificationInputV2Schema(
            payload=ClassroomScheduleFocusNotificationPayloadSchema(
                kind=NotificationKind.CLASSROOM_EVENT_REPETITION_UPDATED_V1,
                classroom_id=classroom_event.classroom_id,
                focused_at=repetition_mode.starts_at,
            ),
            recipient_filters=[
                ClassroomParticipantRecipientFilterSchema(
                    classroom_id=classroom_event.classroom_id,
                    role=ClassroomRole.STUDENT,
                )
            ],
        )
    )

    return repetition_mode


@router.post(
    path="/roles/tutor/classrooms/{classroom_id}/events/{event_id}/cancellations/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel a repeating classroom event by id after some timestamp",
)
async def cancel_repeating_event_after_timestamp(
    classroom_event: MyClassroomEventByIDs,
    starts_at: Annotated[AwareDatetime, Body(embed=True)],
) -> None:
    await cancel_repetition_modes_after_timestamp(
        classroom_event=classroom_event,
        timestamp=starts_at,
    )

    await notifications_bridge.send_notification(
        NotificationInputV2Schema(
            payload=ClassroomScheduleFocusNotificationPayloadSchema(
                kind=NotificationKind.CLASSROOM_EVENT_REPETITION_CANCELLED_V1,
                classroom_id=classroom_event.classroom_id,
                focused_at=starts_at,
            ),
            recipient_filters=[
                ClassroomParticipantRecipientFilterSchema(
                    classroom_id=classroom_event.classroom_id,
                    role=ClassroomRole.STUDENT,
                )
            ],
        )
    )


@router.delete(
    path="/roles/tutor/classrooms/{classroom_id}/events/{event_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a classroom event by ids",
)
async def delete_classroom_event(classroom_event: MyClassroomEventByIDs) -> None:
    await classroom_event.delete()
