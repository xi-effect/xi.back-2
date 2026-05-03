from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from typing import Annotated, assert_never, cast
from uuid import UUID

from fastapi import Path
from pydantic import AwareDatetime
from sqlalchemy import and_, or_, select, tuple_
from sqlalchemy.orm import raiseload

from app.common.config_bdg import classrooms_bridge
from app.common.dependencies.authorization_dep import AuthorizationData
from app.common.fastapi_ext import APIRouterExt
from app.common.sqlalchemy_ext import db
from app.scheduler.dependencies.events_dep import (
    EventTimeFrameQuery,
    EventTimeFrameSchema,
)
from app.scheduler.models.event_instances_db import (
    AnyEventInstance,
    EventInstance,
    EventInstanceKind,
    EventInstanceResponseSchema,
    PersistedRepeatedEventInstanceResponseSchema,
    RepeatedEventInstance,
    SoleEventInstance,
    SoleEventInstanceResponseSchema,
    VirtualRepeatedEventInstanceResponseSchema,
)
from app.scheduler.models.events_db import ClassroomEvent
from app.scheduler.models.repetition_modes_db import (
    ConcreteRepetitionModeClasses,
    RepetitionMode,
)

router = APIRouterExt(tags=["classroom schedules"])


# TODO (170) naming: `_range`???


async def get_repetition_modes_in_range(
    classroom_ids: list[int],
    happens_after: datetime,
    happens_before: datetime,
) -> list[RepetitionMode]:
    return await db.get_all_with_assumed_limit(
        select(RepetitionMode)
        .options(raiseload(RepetitionMode.event))
        .join(ClassroomEvent)
        .filter(
            ClassroomEvent.classroom_id.in_(classroom_ids),
            or_(
                *(
                    and_(
                        *klass.iter_in_range_conditions(
                            happens_after=happens_after,
                            happens_before=happens_before,
                        )
                    )
                    for klass in ConcreteRepetitionModeClasses
                )
            ),
        ),
        limit=1000,
    )


@dataclass(frozen=True)
class VirtualRepeatedEventInstanceKeyData:
    repetition_mode_id: UUID
    instance_index: int


@dataclass(frozen=True)
class VirtualRepeatedEventInstanceValueData:
    starts_at: AwareDatetime
    ends_at: AwareDatetime
    event_id: int


def iter_virtual_repeated_event_instances_in_range(
    repetition_modes: list[RepetitionMode],
    happens_after: datetime,
    happens_before: datetime,
) -> Iterator[
    tuple[
        VirtualRepeatedEventInstanceKeyData,
        VirtualRepeatedEventInstanceValueData,
    ]
]:
    for repetition_mode in repetition_modes:
        event_instance_duration = repetition_mode.event_instance_duration
        yield from (
            (
                VirtualRepeatedEventInstanceKeyData(
                    repetition_mode_id=repetition_mode.id,
                    instance_index=instance_index,
                ),
                VirtualRepeatedEventInstanceValueData(
                    starts_at=starts_at,
                    ends_at=starts_at + event_instance_duration,
                    event_id=repetition_mode.event_id,
                ),
            )
            for (
                instance_index,
                starts_at,
            ) in repetition_mode.iter_event_instances_in_range(
                happens_after=happens_after,
                happens_before=happens_before,
            )
        )


async def get_event_instances_in_range(
    classroom_ids: list[int],
    happens_after: datetime,
    happens_before: datetime,
    virtual_repeated_instance_keys: list[VirtualRepeatedEventInstanceKeyData],
) -> list[AnyEventInstance]:
    filters_or = [
        and_(
            RepeatedEventInstance.kind == EventInstanceKind.SOLE,
            SoleEventInstance.starts_at <= happens_before,
            SoleEventInstance.ends_at > happens_after,
        ),
        and_(
            RepeatedEventInstance.kind == EventInstanceKind.REPEATED,
            RepeatedEventInstance.starts_at_override.is_not(None),
            RepeatedEventInstance.ends_at_override.is_not(None),
            RepeatedEventInstance.starts_at_override <= happens_before,
            RepeatedEventInstance.ends_at_override > happens_after,
        ),
    ]
    if len(virtual_repeated_instance_keys) > 0:
        filters_or.append(
            and_(
                RepeatedEventInstance.kind == EventInstanceKind.REPEATED,
                tuple_(
                    RepeatedEventInstance.repetition_mode_id,
                    RepeatedEventInstance.instance_index,
                ).in_(
                    [
                        (key.repetition_mode_id, key.instance_index)
                        for key in virtual_repeated_instance_keys
                    ]
                ),
            )
        )

    return cast(  # no good way to type this in SQLAlchemy
        list[AnyEventInstance],
        await db.get_all_with_assumed_limit(
            select(EventInstance)
            .options(
                raiseload(EventInstance.event),
                # TODO enable `raiseload` for `RepeatedEventInstance.repetition_mode`
                #   Currently disabled for generating virtual event in `iter_persisted_repeated_event_instances`
            )
            .join(ClassroomEvent)
            .filter(
                ClassroomEvent.classroom_id.in_(classroom_ids),
                or_(*filters_or),
            ),
            limit=1000,
        ),
    )


class ScheduleResponseSchemaAdapter:
    def __init__(
        self,
        events_by_id: dict[int, ClassroomEvent],
        sole_event_instances: list[SoleEventInstance],
        persisted_repeated_event_instances: list[RepeatedEventInstance],
        persisted_repeated_event_instance_keys: set[
            VirtualRepeatedEventInstanceKeyData
        ],
        virtual_repeated_instances_by_id: dict[
            VirtualRepeatedEventInstanceKeyData,
            VirtualRepeatedEventInstanceValueData,
        ],
    ) -> None:
        self.events_by_id = events_by_id
        self.virtual_repeated_instances_by_id = virtual_repeated_instances_by_id
        self.sole_event_instances = sole_event_instances
        self.persisted_repeated_event_instances = persisted_repeated_event_instances
        self.persisted_repeated_event_instance_keys = (
            persisted_repeated_event_instance_keys
        )

    def iter_sole_event_instances(self) -> Iterator[SoleEventInstanceResponseSchema]:
        for sole_event_instance in self.sole_event_instances:
            event = self.events_by_id[sole_event_instance.event_id]
            yield SoleEventInstanceResponseSchema(
                id=sole_event_instance.id,
                event_id=event.id,
                classroom_id=event.classroom_id,
                cancelled_at=sole_event_instance.cancelled_at,
                starts_at=sole_event_instance.starts_at,
                ends_at=sole_event_instance.ends_at,
                name=event.name,
                description=event.description,
            )

    def iter_persisted_repeated_event_instances(
        self,
    ) -> Iterator[PersistedRepeatedEventInstanceResponseSchema]:
        for (
            persisted_repeated_event_instance
        ) in self.persisted_repeated_event_instances:
            event = self.events_by_id[persisted_repeated_event_instance.event_id]

            virtual_event_instance_value = self.virtual_repeated_instances_by_id.get(
                VirtualRepeatedEventInstanceKeyData(
                    repetition_mode_id=persisted_repeated_event_instance.repetition_mode_id,
                    instance_index=persisted_repeated_event_instance.instance_index,
                )
            )
            if virtual_event_instance_value is None:
                repetition_mode = persisted_repeated_event_instance.repetition_mode
                starts_at = (
                    repetition_mode.calculate_event_instance_starts_at_for_index(
                        instance_index=persisted_repeated_event_instance.instance_index,
                    )
                )
                virtual_event_instance_value = VirtualRepeatedEventInstanceValueData(
                    starts_at=starts_at,
                    ends_at=starts_at + repetition_mode.event_instance_duration,
                    event_id=event.id,
                )

            yield PersistedRepeatedEventInstanceResponseSchema(
                id=persisted_repeated_event_instance.id,
                event_id=event.id,
                classroom_id=event.classroom_id,
                repetition_mode_id=persisted_repeated_event_instance.repetition_mode_id,
                instance_index=persisted_repeated_event_instance.instance_index,
                cancelled_at=persisted_repeated_event_instance.cancelled_at,
                starts_at=(
                    persisted_repeated_event_instance.starts_at_override
                    or virtual_event_instance_value.starts_at
                ),
                ends_at=(
                    persisted_repeated_event_instance.ends_at_override
                    or virtual_event_instance_value.ends_at
                ),
                name=persisted_repeated_event_instance.name_override or event.name,
                description=(
                    persisted_repeated_event_instance.description_override
                    or event.description
                ),
            )

    def iter_virtual_repeated_event_instances(
        self,
    ) -> Iterator[VirtualRepeatedEventInstanceResponseSchema]:
        for (
            virtual_repeated_event_instance_key,
            virtual_repeated_event_instance_value,
        ) in self.virtual_repeated_instances_by_id.items():
            if (
                virtual_repeated_event_instance_key
                in self.persisted_repeated_event_instance_keys
            ):
                continue

            event = self.events_by_id[virtual_repeated_event_instance_value.event_id]
            yield VirtualRepeatedEventInstanceResponseSchema(
                event_id=event.id,
                classroom_id=event.classroom_id,
                repetition_mode_id=virtual_repeated_event_instance_key.repetition_mode_id,
                instance_index=virtual_repeated_event_instance_key.instance_index,
                starts_at=virtual_repeated_event_instance_value.starts_at,
                ends_at=virtual_repeated_event_instance_value.ends_at,
                name=event.name,
                description=event.description,
            )

    def iter_event_instances(self) -> Iterator[EventInstanceResponseSchema]:
        yield from self.iter_sole_event_instances()
        yield from self.iter_persisted_repeated_event_instances()
        yield from self.iter_virtual_repeated_event_instances()

    def adapt(self) -> list[EventInstanceResponseSchema]:
        return list(self.iter_event_instances())


async def list_classroom_event_instances(
    classroom_ids: list[int],
    time_frame: EventTimeFrameSchema,
) -> list[EventInstanceResponseSchema]:
    repetition_modes = await get_repetition_modes_in_range(
        classroom_ids=classroom_ids,
        happens_after=time_frame.happens_after,
        happens_before=time_frame.happens_before,
    )

    virtual_repeated_instances_by_id: dict[
        VirtualRepeatedEventInstanceKeyData,
        VirtualRepeatedEventInstanceValueData,
    ] = dict(
        iter_virtual_repeated_event_instances_in_range(
            repetition_modes=repetition_modes,
            happens_after=time_frame.happens_after,
            happens_before=time_frame.happens_before,
        )
    )

    persisted_event_instances = await get_event_instances_in_range(
        classroom_ids=classroom_ids,
        happens_after=time_frame.happens_after,
        happens_before=time_frame.happens_before,
        virtual_repeated_instance_keys=list(virtual_repeated_instances_by_id.keys()),
    )

    sole_event_instances: list[SoleEventInstance] = []
    persisted_repeated_event_instances: list[RepeatedEventInstance] = []

    for persisted_event_instance in persisted_event_instances:
        match persisted_event_instance:
            case SoleEventInstance():
                if (
                    persisted_event_instance.cancelled_at is not None
                    or persisted_event_instance.starts_at > time_frame.happens_before
                    or persisted_event_instance.ends_at <= time_frame.happens_after
                ):
                    continue
                sole_event_instances.append(persisted_event_instance)
            case RepeatedEventInstance():
                if (
                    persisted_event_instance.cancelled_at is not None
                    or (
                        persisted_event_instance.starts_at_override is not None
                        and persisted_event_instance.starts_at_override
                        > time_frame.happens_before
                    )
                    or (
                        persisted_event_instance.ends_at_override is not None
                        and persisted_event_instance.ends_at_override
                        <= time_frame.happens_after
                    )
                ):
                    virtual_repeated_instances_by_id.pop(
                        VirtualRepeatedEventInstanceKeyData(
                            persisted_event_instance.repetition_mode_id,
                            persisted_event_instance.instance_index,
                        ),
                        None,
                    )
                    continue
                persisted_repeated_event_instances.append(persisted_event_instance)
            case _:
                assert_never(persisted_event_instance)

    persisted_repeated_event_instance_keys: set[VirtualRepeatedEventInstanceKeyData] = {
        VirtualRepeatedEventInstanceKeyData(
            repetition_mode_id=event_instance.repetition_mode_id,
            instance_index=event_instance.instance_index,
        )
        for event_instance in persisted_repeated_event_instances
    }

    repetition_mode_ids_used_in_event_instances: set[UUID] = {
        key.repetition_mode_id
        for key in (
            *virtual_repeated_instances_by_id.keys(),
            *persisted_repeated_event_instance_keys,
        )
    }

    event_ids: list[int] = list(
        {
            repetition_mode.event_id
            for repetition_mode in repetition_modes
            if repetition_mode.id in repetition_mode_ids_used_in_event_instances
        }
        | {event_instance.event_id for event_instance in sole_event_instances}
        | {
            event_instance.event_id
            for event_instance in persisted_repeated_event_instances
        }
    )

    events_by_id: dict[int, ClassroomEvent]
    if len(event_ids) == 0:
        events_by_id = {}
    else:
        events_by_id = {
            classroom_event.id: classroom_event
            for classroom_event in await ClassroomEvent.find_all_by_ids(
                event_ids=event_ids
            )
        }

    return ScheduleResponseSchemaAdapter(
        events_by_id=events_by_id,
        virtual_repeated_instances_by_id=virtual_repeated_instances_by_id,
        sole_event_instances=sole_event_instances,
        persisted_repeated_event_instances=persisted_repeated_event_instances,
        persisted_repeated_event_instance_keys=persisted_repeated_event_instance_keys,
    ).adapt()


@router.get(
    path="/roles/tutor/classrooms/{classroom_id}/schedule/",
    summary="Retrieve a schedule for all of the events in a classroom by id",
)
@router.get(
    path="/roles/student/classrooms/{classroom_id}/schedule/",
    summary="Retrieve a schedule for all of the events in a classroom by id",
)
async def retrieve_classroom_schedule(
    classroom_id: Annotated[int, Path()],
    time_frame: EventTimeFrameQuery,
) -> list[EventInstanceResponseSchema]:
    return await list_classroom_event_instances(
        classroom_ids=[classroom_id],
        time_frame=time_frame,
    )


@router.get(
    path="/roles/tutor/schedule/",
    summary="Retrieve a schedule for all events for the current tutor",
)
async def retrieve_tutor_schedule(
    auth_data: AuthorizationData,
    time_frame: EventTimeFrameQuery,
) -> list[EventInstanceResponseSchema]:
    return await list_classroom_event_instances(
        classroom_ids=await classrooms_bridge.list_tutor_classroom_ids(
            tutor_id=auth_data.user_id
        ),
        time_frame=time_frame,
    )


@router.get(
    path="/roles/student/schedule/",
    summary="Retrieve a schedule for all events for the current student",
)
async def retrieve_student_schedule(
    auth_data: AuthorizationData,
    time_frame: EventTimeFrameQuery,
) -> list[EventInstanceResponseSchema]:
    return await list_classroom_event_instances(
        classroom_ids=await classrooms_bridge.list_student_classroom_ids(
            student_id=auth_data.user_id
        ),
        time_frame=time_frame,
    )
