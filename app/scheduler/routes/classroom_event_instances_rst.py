from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, Field
from starlette import status

from app.common.fastapi_ext import APIRouterExt, Responses
from app.common.utils.datetime import datetime_utc_now
from app.scheduler.dependencies.event_instances_dep import (
    ClassroomEventByInstanceID,
    EventInstanceIndex,
    MyClassroomEventInstanceByIDs,
)
from app.scheduler.dependencies.repetition_modes_dep import (
    ClassroomEventByRepetitionModeID,
    MyClassroomRepetitionModeByIDs,
)
from app.scheduler.models.event_instances_db import (
    EventInstanceResponseSchemaKind,
    EventInstanceTimeSlotInputSchema,
    RepeatedEventInstance,
    SoleEventInstance,
)
from app.scheduler.models.events_db import ClassroomEvent
from app.scheduler.models.repetition_modes_db import (
    RepetitionModeResponseSchema,
    REPETITION_MODE_TYPE_ADAPTER,
)

router = APIRouterExt(tags=["classroom event instances"])


class VirtualRepeatedEventInstanceStandaloneResponseSchema(BaseModel):
    starts_at: AwareDatetime
    ends_at: AwareDatetime


class BaseEventInstanceDetailedResponseSchema(BaseModel):
    event: ClassroomEvent.ResponseSchema


class SoleEventInstanceDetailedResponseSchema(BaseEventInstanceDetailedResponseSchema):
    kind: Literal[EventInstanceResponseSchemaKind.SOLE] = (
        EventInstanceResponseSchemaKind.SOLE
    )

    persisted_event_instance: SoleEventInstance.StandaloneResponseSchema


class BaseRepeatedEventInstanceDetailedResponseSchema(
    BaseEventInstanceDetailedResponseSchema
):
    repetition_mode: RepetitionModeResponseSchema
    instance_index: int

    virtual_event_instance: VirtualRepeatedEventInstanceStandaloneResponseSchema


class PersistedRepeatedEventInstanceDetailedResponseSchema(
    BaseRepeatedEventInstanceDetailedResponseSchema
):
    kind: Literal[EventInstanceResponseSchemaKind.REPEATED_PERSISTED] = (
        EventInstanceResponseSchemaKind.REPEATED_PERSISTED
    )

    persisted_event_instance: RepeatedEventInstance.StandaloneResponseSchema


class VirtualRepeatedEventInstanceDetailedResponseSchema(
    BaseRepeatedEventInstanceDetailedResponseSchema
):
    kind: Literal[EventInstanceResponseSchemaKind.REPEATED_VIRTUAL] = (
        EventInstanceResponseSchemaKind.REPEATED_VIRTUAL
    )


EventInstanceDetailedResponseSchema = Annotated[
    SoleEventInstanceDetailedResponseSchema
    | PersistedRepeatedEventInstanceDetailedResponseSchema
    | VirtualRepeatedEventInstanceDetailedResponseSchema,
    Field(discriminator="kind"),
]


@router.get(
    path=(
        "/roles/tutor/classrooms/{classroom_id}"
        "/event-instances/{event_instance_id}"
        "/"
    ),
    summary="Retrieve detailed data for any classroom event instance by id",
)
@router.get(
    path=(
        "/roles/student/classrooms/{classroom_id}"
        "/event-instances/{event_instance_id}"
        "/"
    ),
    summary="Retrieve detailed data for any classroom event instance by id",
)
async def retrieve_detailed_classroom_event_instance(
    classroom_event: ClassroomEventByInstanceID,
    event_instance: MyClassroomEventInstanceByIDs,
) -> EventInstanceDetailedResponseSchema:
    # TODO (170) move to _schedules_rst? XOR move common logic to "svc"
    match event_instance:
        case SoleEventInstance():
            return SoleEventInstanceDetailedResponseSchema(
                event=ClassroomEvent.ResponseSchema.model_validate(
                    classroom_event,
                    from_attributes=True,
                ),
                persisted_event_instance=SoleEventInstance.StandaloneResponseSchema.model_validate(
                    event_instance,
                    from_attributes=True,
                ),
            )
        case RepeatedEventInstance():
            virtual_instance_starts_at = event_instance.repetition_mode.calculate_event_instance_starts_at_for_index(
                instance_index=event_instance.instance_index,
            )
            return PersistedRepeatedEventInstanceDetailedResponseSchema(
                event=ClassroomEvent.ResponseSchema.model_validate(
                    classroom_event, from_attributes=True
                ),
                repetition_mode=REPETITION_MODE_TYPE_ADAPTER.validate_python(
                    event_instance.repetition_mode,
                    from_attributes=True,
                ),
                instance_index=event_instance.instance_index,
                virtual_event_instance=VirtualRepeatedEventInstanceStandaloneResponseSchema(
                    starts_at=virtual_instance_starts_at,
                    ends_at=(
                        virtual_instance_starts_at
                        + event_instance.repetition_mode.event_instance_duration
                    ),
                ),
                persisted_event_instance=RepeatedEventInstance.StandaloneResponseSchema.model_validate(
                    event_instance, from_attributes=True
                ),
            )


@router.get(
    path=(
        "/roles/tutor/classrooms/{classroom_id}"
        "/repetition-modes/{repetition_mode_id}"
        "/instances/{instance_index}"
        "/"
    ),
    summary="Retrieve detailed data for any classroom event instance in a repetition mode by id and index",
)
@router.get(
    path=(
        "/roles/student/classrooms/{classroom_id}"
        "/repetition-modes/{repetition_mode_id}"
        "/instances/{instance_index}"
        "/"
    ),
    summary="Retrieve detailed data for any classroom event instance in a repetition mode by id and index",
)
async def retrieve_detailed_repeated_classroom_event_instance(
    classroom_event: ClassroomEventByRepetitionModeID,
    repetition_mode: MyClassroomRepetitionModeByIDs,
    instance_index: EventInstanceIndex,
) -> EventInstanceDetailedResponseSchema:
    # TODO (170) DRY (aaaaaaaaaaaa)
    # TODO (170) move to _schedules_rst? XOR move common logic to "svc"
    event_instance = await RepeatedEventInstance.find_by_repetition_mode_id_and_index(
        repetition_mode_id=repetition_mode.id,
        instance_index=instance_index,
    )

    response_schema: type[
        VirtualRepeatedEventInstanceDetailedResponseSchema
        | PersistedRepeatedEventInstanceDetailedResponseSchema
    ] = (
        VirtualRepeatedEventInstanceDetailedResponseSchema
        if event_instance is None
        else PersistedRepeatedEventInstanceDetailedResponseSchema
    )

    virtual_instance_starts_at = (  # TODO (170) restructure better
        repetition_mode.calculate_event_instance_starts_at_for_index(
            instance_index=instance_index,
        )
    )
    return response_schema(
        event=ClassroomEvent.ResponseSchema.model_validate(
            classroom_event,
            from_attributes=True,
        ),
        repetition_mode=REPETITION_MODE_TYPE_ADAPTER.validate_python(
            repetition_mode,
            from_attributes=True,
        ),
        instance_index=instance_index,
        virtual_event_instance=VirtualRepeatedEventInstanceStandaloneResponseSchema(
            starts_at=virtual_instance_starts_at,
            ends_at=(
                virtual_instance_starts_at + repetition_mode.event_instance_duration
            ),
        ),
        persisted_event_instance=(  # type: ignore[call-arg]
            None
            if event_instance is None
            else RepeatedEventInstance.StandaloneResponseSchema.model_validate(
                event_instance,
                from_attributes=True,
            )
        ),
    )


@router.put(
    path=(
        "/roles/tutor/classrooms/{classroom_id}"
        "/event-instances/{event_instance_id}"
        "/time-slot/"
    ),
    status_code=status.HTTP_204_NO_CONTENT,  # TODO (170) response schema
    summary="Reschedule any classroom event instance by id",
)
async def reschedule_persisted_classroom_event_instance(
    event_instance: MyClassroomEventInstanceByIDs,
    data: EventInstanceTimeSlotInputSchema,
) -> None:
    event_instance.reschedule(
        new_starts_at=data.starts_at,
        new_ends_at=data.ends_at,
    )


@router.put(
    path=(
        "/roles/tutor/classrooms/{classroom_id}"
        "/repetition-modes/{repetition_mode_id}"
        "/instances/{instance_index}"
        "/time-slot/"
    ),
    status_code=status.HTTP_204_NO_CONTENT,  # TODO (170) response schema
    summary="Reschedule any classroom event instance in a repetition mode by id and index",
)
async def reschedule_repeated_classroom_event_instance(
    repetition_mode: MyClassroomRepetitionModeByIDs,
    instance_index: EventInstanceIndex,
    data: EventInstanceTimeSlotInputSchema,
) -> None:
    # TODO (170) DRY (repeated in cancel_repeated_classroom_event_instance)
    event_instance = await RepeatedEventInstance.find_by_repetition_mode_id_and_index(
        repetition_mode_id=repetition_mode.id,
        instance_index=instance_index,
    )
    if event_instance is None:
        # TODO (170) generate the actual event instance and check it's not outside of the range
        # TODO (170) check new time-slot is not equal to the generated one
        await RepeatedEventInstance.create(
            event_id=repetition_mode.event_id,
            repetition_mode_id=repetition_mode.id,
            instance_index=instance_index,
            starts_at_override=data.starts_at,
            ends_at_override=data.ends_at,
        )
        # TODO(?)
        #   `event_instance = await create(...)`
        #   `event_instance.reschedule(...)`
    else:
        event_instance.reschedule(
            new_starts_at=data.starts_at,
            new_ends_at=data.ends_at,
        )


class EventInstanceCancellationResponses(Responses):
    EVENT_INSTANCE_ALREADY_CANCELLED = (
        status.HTTP_409_CONFLICT,
        "Event instance already cancelled",
    )


@router.post(
    path=(
        "/roles/tutor/classrooms/{classroom_id}"
        "/event-instances/{event_instance_id}"
        "/cancellation/"
    ),
    status_code=status.HTTP_201_CREATED,  # TODO (170) mb a response schema
    responses=EventInstanceCancellationResponses.responses(),
    summary="Cancel any classroom event instance by id",
)
async def cancel_persisted_classroom_event_instance(
    event_instance: MyClassroomEventInstanceByIDs,
) -> None:
    if event_instance.cancelled_at is not None:
        raise EventInstanceCancellationResponses.EVENT_INSTANCE_ALREADY_CANCELLED
    event_instance.cancelled_at = datetime_utc_now()


@router.post(
    path=(
        "/roles/tutor/classrooms/{classroom_id}"
        "/repetition-modes/{repetition_mode_id}"
        "/instances/{instance_index}"
        "/cancellation/"
    ),
    status_code=status.HTTP_201_CREATED,  # TODO (170) mb a response schema
    responses=EventInstanceCancellationResponses.responses(),
    summary="Cancel any classroom event instance in a repetition mode by id and index",
)
async def cancel_repeated_classroom_event_instance(
    repetition_mode: MyClassroomRepetitionModeByIDs,
    instance_index: EventInstanceIndex,
) -> None:
    event_instance = await RepeatedEventInstance.find_by_repetition_mode_id_and_index(
        repetition_mode_id=repetition_mode.id,
        instance_index=instance_index,
    )
    if event_instance is None:
        # TODO (170) generate the actual event instance and check it's not outside of the range
        await RepeatedEventInstance.create(
            event_id=repetition_mode.event_id,
            repetition_mode_id=repetition_mode.id,
            instance_index=instance_index,
            cancelled_at=datetime_utc_now(),
        )
    elif event_instance.cancelled_at is not None:
        raise EventInstanceCancellationResponses.EVENT_INSTANCE_ALREADY_CANCELLED
    else:
        event_instance.cancelled_at = datetime_utc_now()


class EventInstanceUncancellationResponses(Responses):
    EVENT_INSTANCE_IS_NOT_CANCELLED = (
        status.HTTP_409_CONFLICT,
        "Event instance is not cancelled",
    )


@router.delete(
    path=(
        "/roles/tutor/classrooms/{classroom_id}"
        "/event-instances/{event_instance_id}"
        "/cancellation/"
    ),
    status_code=status.HTTP_204_NO_CONTENT,  # TODO (170) mb a response schema
    responses=EventInstanceUncancellationResponses.responses(),
    summary="Uncancel any classroom event instance by id",
)
async def uncancel_persisted_classroom_event_instance(
    event_instance: MyClassroomEventInstanceByIDs,
) -> None:
    if event_instance.cancelled_at is None:
        raise EventInstanceUncancellationResponses.EVENT_INSTANCE_IS_NOT_CANCELLED

    event_instance.cancelled_at = None
