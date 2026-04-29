from starlette import status

from app.common.fastapi_ext import APIRouterExt, Responses
from app.common.utils.datetime import datetime_utc_now
from app.scheduler.dependencies.event_instances_dep import (
    EventInstanceIndex,
    MyClassroomEventInstanceByIDs,
)
from app.scheduler.dependencies.repetition_modes_dep import (
    MyClassroomRepetitionModeByIDs,
)
from app.scheduler.models.event_instances_db import (
    EventInstanceTimeSlotInputSchema,
    RepeatedEventInstance,
)

router = APIRouterExt(tags=["classroom event instances"])


@router.put(
    path=(
        "/roles/tutor/classrooms/{classroom_id}"
        "/event-instances/{event_instance_id}"
        "/time-slot/"
    ),
    status_code=status.HTTP_204_NO_CONTENT,  # TODO: response schema
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
    status_code=status.HTTP_204_NO_CONTENT,  # TODO: response schema
    summary="Reschedule any classroom event instance in a repetition mode by id and index",
)
async def reschedule_repeated_classroom_event_instance(
    repetition_mode: MyClassroomRepetitionModeByIDs,
    instance_index: EventInstanceIndex,
    data: EventInstanceTimeSlotInputSchema,
) -> None:
    # TODO: DRY (repeated in cancel_repeated_classroom_event_instance)
    event_instance = await RepeatedEventInstance.find_by_repetition_mode_id_and_index(
        repetition_mode_id=repetition_mode.id,
        instance_index=instance_index,
    )
    if event_instance is None:
        # TODO generate the actual event instance and check it's not outside of the range
        # TODO check new time-slot is not equal to the generated one
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
    status_code=status.HTTP_201_CREATED,  # TODO: mb a response schema
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
    status_code=status.HTTP_201_CREATED,  # TODO: mb a response schema
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
        # TODO generate the actual event instance and check it's not outside of the range
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
    status_code=status.HTTP_204_NO_CONTENT,  # TODO: mb a response schema
    responses=EventInstanceUncancellationResponses.responses(),
    summary="Uncancel any classroom event instance by id",
)
async def uncancel_persisted_classroom_event_instance(
    event_instance: MyClassroomEventInstanceByIDs,
) -> None:
    if event_instance.cancelled_at is None:
        raise EventInstanceUncancellationResponses.EVENT_INSTANCE_IS_NOT_CANCELLED

    event_instance.cancelled_at = None
