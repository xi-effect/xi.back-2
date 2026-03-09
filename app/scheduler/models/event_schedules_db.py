from datetime import datetime
from enum import StrEnum, auto
from typing import Annotated, Literal, Self

from pydantic import AwareDatetime, Field, PositiveInt, model_validator
from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import SMALLINT, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.config import Base
from app.scheduler.models.events_db import Event


class EventScheduleKind(StrEnum):
    ONCE = auto()
    WEEKLY = auto()


class EventSchedule(Base):
    __tablename__: str | None = "event_schedules"

    id: Mapped[int] = mapped_column(primary_key=True)

    event_id: Mapped[int] = mapped_column(ForeignKey(Event.id))
    kind: Mapped[EventScheduleKind] = mapped_column(ENUM(EventScheduleKind))

    event: Mapped[Event] = relationship(back_populates="schedules")

    __mapper_args__ = {
        "polymorphic_on": kind,
        "polymorphic_abstract": True,
        "with_polymorphic": "*",
    }

    BaseResponseSchema = MappedModel.create(columns=[id, event_id])


class OnceEventSchedule(EventSchedule):
    __tablename__ = None

    __mapper_args__ = {
        "polymorphic_identity": EventScheduleKind.ONCE,
        "polymorphic_load": "inline",
    }

    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    duration_minutes: Mapped[int] = mapped_column()
    BaseInputSchema = MappedModel.create(
        columns=[(starts_at, AwareDatetime), (duration_minutes, PositiveInt)],
    )
    InputSchema = BaseInputSchema.extend(
        extra_fields={
            "kind": (Literal[EventScheduleKind.ONCE], EventScheduleKind.ONCE),
        }
    )
    ResponseSchema = InputSchema.extend(
        bases=[
            EventSchedule.BaseResponseSchema,
        ],
    )


class BaseRecurringEventSchedule(OnceEventSchedule):
    __tablename__ = None

    __mapper_args__ = {"polymorphic_identity": None}

    valid_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )

    InputSchema = MappedModel.create(
        columns=[(valid_until, AwareDatetime | None)],
        bases=[OnceEventSchedule.BaseInputSchema],
    )


class WeeklyEventSchedule(BaseRecurringEventSchedule):
    __tablename__ = None

    __mapper_args__ = {
        "polymorphic_identity": EventScheduleKind.WEEKLY,
        "polymorphic_load": "inline",
    }

    day_of_week: Mapped[int] = mapped_column(SMALLINT(), nullable=True)

    DayOfWeekType = Annotated[int, Field(ge=1, le=7)]

    InputSchema = MappedModel.create(
        bases=[BaseRecurringEventSchedule.InputSchema],
        columns=[(day_of_week, DayOfWeekType)],
        extra_fields={
            "kind": (Literal[EventScheduleKind.WEEKLY], EventScheduleKind.WEEKLY),
        },
    )
    ResponseSchema = InputSchema.extend(
        bases=[EventSchedule.BaseResponseSchema],
    )


class WeeklyEventScheduleInputSchema(WeeklyEventSchedule.InputSchema):
    @model_validator(mode="after")
    def validate_day_of_week_from_starts_at(self) -> Self:
        if self.starts_at.isoweekday() != self.day_of_week:
            raise ValueError("day of week must match starts_at weekday")
        if self.valid_until is not None and self.starts_at >= self.valid_until:
            raise ValueError("valid_until must be later then starts_at")
        return self


AnyEventSchedule = OnceEventSchedule | WeeklyEventSchedule

EventSchedulesInputSchema = Annotated[
    OnceEventSchedule.InputSchema | WeeklyEventScheduleInputSchema,
    Field(discriminator="kind"),
]

EventSchedulesResponseSchema = Annotated[
    OnceEventSchedule.ResponseSchema | WeeklyEventSchedule.ResponseSchema,
    Field(discriminator="kind"),
]
