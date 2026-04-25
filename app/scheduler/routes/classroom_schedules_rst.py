import logging
from collections.abc import Iterator
from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import Path
from pydantic import AwareDatetime, BaseModel, TypeAdapter
from pydantic_marshals.base import CompositeMarshalModel
from sqlalchemy import and_, or_, select

from app.common.fastapi_ext import APIRouterExt
from app.common.sqlalchemy_ext import db
from app.scheduler.dependencies.events_dep import EventTimeFrameQuery
from app.scheduler.models.events_db import ClassroomEvent
from app.scheduler.models.occurrence_modes_db import (
    ConcreteOccurrenceModeClasses,
    OccurrenceMode,
    OccurrenceModePolymorphic,
    OccurrenceModeResponseSchema,
)

router = APIRouterExt(tags=["classroom schedules"])


class EventInstanceResponseSchema(BaseModel):
    id: int
    starts_at: AwareDatetime
    ends_at: AwareDatetime
    occurrence_mode_id: UUID


class ScheduleResponseSchema(CompositeMarshalModel):
    events: list[Annotated[ClassroomEvent, ClassroomEvent.ResponseSchema]]
    occurrence_modes: list[OccurrenceModeResponseSchema]
    event_instances: list[EventInstanceResponseSchema]


occurrence_modes_type_adapter = TypeAdapter(list[OccurrenceModeResponseSchema])


def convert_timestamp_to_naive_utc(timestamp: datetime) -> datetime:
    return timestamp.astimezone(tz=timezone.utc).replace(tzinfo=None)


async def get_occurrence_modes(
    classroom_id: int,
    happens_after_utc: datetime,
    happens_before_utc: datetime,
) -> list[OccurrenceMode]:
    stmt = (
        select(OccurrenceModePolymorphic)
        .join(ClassroomEvent)
        .filter_by(classroom_id=classroom_id)
        .filter(
            or_(
                *(
                    and_(
                        *klass.iter_in_range_conditions(
                            happens_after_utc, happens_before_utc
                        )
                    )
                    for klass in ConcreteOccurrenceModeClasses
                )
            )
        )
        .limit(1000)
    )

    result = list(await db.get_all(stmt))

    if len(result) == 1000:
        logging.warning(
            "Reached the limit of 1000 occurrence modes in one query",
            extra={
                "happens_after_utc": happens_after_utc,
                "happens_before_utc": happens_before_utc,
                "classroom_id": classroom_id,
            },
        )

    return result


def iter_event_instances(
    occurrence_modes: list[OccurrenceMode],
    happens_after_utc: datetime,
    happens_before_utc: datetime,
) -> Iterator[EventInstanceResponseSchema]:
    for occurrence_mode in occurrence_modes:
        event_instance_duration = occurrence_mode.event_instance_duration

        for (
            event_instance_id,
            starts_at_utc,
        ) in occurrence_mode.iter_event_instances_in_range(
            happens_after_utc=happens_after_utc,
            happens_before_utc=happens_before_utc,
        ):
            starts_at = starts_at_utc.replace(tzinfo=timezone.utc)
            yield EventInstanceResponseSchema(
                id=event_instance_id,
                starts_at=starts_at,
                ends_at=starts_at + event_instance_duration,
                occurrence_mode_id=occurrence_mode.id,
            )


@router.get(
    path="/roles/tutor/classrooms/{classroom_id}/schedule/",
    response_model=ScheduleResponseSchema.build_marshal(),
    summary="Retrieve a schedule for all of the events in a classroom by id",
)
@router.get(
    path="/roles/student/classrooms/{classroom_id}/schedule/",
    response_model=ScheduleResponseSchema.build_marshal(),
    summary="Retrieve a schedule for all of the events in a classroom by id",
)
async def list_classroom_events(
    classroom_id: Annotated[int, Path()],
    time_frame: EventTimeFrameQuery,
) -> ScheduleResponseSchema:
    happens_after_utc, happens_before_utc = (
        convert_timestamp_to_naive_utc(time_frame.happens_after),
        convert_timestamp_to_naive_utc(time_frame.happens_before),
    )

    occurrence_modes = await get_occurrence_modes(
        classroom_id=classroom_id,
        happens_after_utc=happens_after_utc,
        happens_before_utc=happens_before_utc,
    )
    events = await ClassroomEvent.find_all_by_ids(
        event_ids=list(
            {occurrence_mode.event_id for occurrence_mode in occurrence_modes}
        )
    )
    event_instances = list(
        iter_event_instances(
            occurrence_modes=occurrence_modes,
            happens_after_utc=happens_after_utc,
            happens_before_utc=happens_before_utc,
        )
    )

    return ScheduleResponseSchema(
        events=list(events),
        # Composite marshal model doesn't support union-models (yet), so the conversion has to be done manually
        occurrence_modes=occurrence_modes_type_adapter.validate_python(
            occurrence_modes
        ),
        event_instances=event_instances,
    )
