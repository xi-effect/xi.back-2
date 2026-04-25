from abc import abstractmethod
from collections.abc import Iterator
from datetime import datetime, timedelta, timezone
from enum import StrEnum, auto
from typing import Annotated, ClassVar, Literal, Self
from uuid import UUID, uuid4

from pydantic import (
    AwareDatetime,
    BaseModel,
    Field,
    NaiveDatetime,
    computed_field,
    model_validator,
)
from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import (
    Enum,
    ForeignKey,
    Index,
    SQLColumnExpression,
    or_,
)
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import (
    InstrumentedAttribute,
    Mapped,
    mapped_column,
    with_polymorphic,
)

from app.common.config import Base
from app.common.utils.bitwise import (
    construct_continuous_bitmask,
)
from app.common.utils.datetime import datetime_utc_now
from app.scheduler.models.events_db import Event
from app.scheduler.utils.bitmasks import (
    PSQLBitmask,
    TimestampRelativeBitmask,
    WeeklyBitmask,
)


class OccurrenceKind(StrEnum):
    SINGLE = auto()
    EXCEPTIONAL = auto()
    DAILY = auto()
    WEEKLY = auto()


class OccurrenceMode(Base):
    __tablename__: str | None = "occurrence_modes"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    event_id: Mapped[int] = mapped_column(
        ForeignKey(Event.id, ondelete="CASCADE"),
        index=True,
    )

    kind: Mapped[OccurrenceKind] = mapped_column(Enum(OccurrenceKind))

    starts_at_utc: Mapped[datetime] = mapped_column(TIMESTAMP(precision=0))
    ends_at_utc: Mapped[datetime] = mapped_column(TIMESTAMP(precision=0))

    __mapper_args__ = {
        "polymorphic_on": kind,
        "polymorphic_abstract": True,
    }

    __table_args__ = (
        Index(
            "index_occurrence_modes_kind_and_interval", kind, starts_at_utc, ends_at_utc
        ),
    )

    @property
    def starts_at(self) -> AwareDatetime:
        return self.starts_at_utc.replace(tzinfo=timezone.utc)

    @property
    def ends_at(self) -> AwareDatetime:
        return self.ends_at_utc.replace(tzinfo=timezone.utc)

    @property
    def duration(self) -> timedelta:
        return self.ends_at_utc - self.starts_at_utc

    @property
    def duration_seconds(self) -> int:
        return self.duration.seconds

    @property
    def event_instance_duration(self) -> timedelta:
        return timedelta(seconds=self.duration_seconds)

    InnerInputSchema = MappedModel.create(
        columns=[(starts_at_utc, NaiveDatetime), (ends_at_utc, NaiveDatetime)],
    )
    ResponseSchema = MappedModel.create(
        columns=[id, event_id], properties=[starts_at, duration_seconds]
    )

    @classmethod
    def iter_in_range_conditions(
        cls,
        happens_after_utc: datetime,
        happens_before_utc: datetime,
    ) -> Iterator[SQLColumnExpression[bool]]:
        yield cls.kind == cls.__mapper__.polymorphic_identity
        yield cls.starts_at_utc < happens_before_utc

    def iter_event_instances_in_range(
        self,
        happens_after_utc: datetime,
        happens_before_utc: datetime,
    ) -> Iterator[tuple[int, datetime]]:
        """This method assumes, that the occurrence mode is inside the range (checked on query level)"""
        raise NotImplementedError


class DiscreteOccurrenceMode(OccurrenceMode):
    __tablename__ = None
    __mapper_args__ = {
        "polymorphic_abstract": True,
    }

    @classmethod
    def iter_in_range_conditions(
        cls,
        happens_after_utc: datetime,
        happens_before_utc: datetime,
    ) -> Iterator[SQLColumnExpression[bool]]:
        yield from super().iter_in_range_conditions(
            happens_after_utc=happens_after_utc,
            happens_before_utc=happens_before_utc,
        )
        yield cls.ends_at_utc >= happens_after_utc

    def iter_event_instances_in_range(
        self,
        happens_after_utc: datetime,
        happens_before_utc: datetime,
    ) -> Iterator[tuple[int, datetime]]:
        yield 0, self.starts_at_utc


class SingleOccurrenceMode(DiscreteOccurrenceMode):
    __tablename__ = None
    __mapper_args__ = {
        "polymorphic_identity": OccurrenceKind.SINGLE,
        "polymorphic_load": "inline",
    }

    ResponseSchema = MappedModel.create(
        bases=[DiscreteOccurrenceMode.ResponseSchema],
        extra_fields={"kind": (Literal[OccurrenceKind.SINGLE], OccurrenceKind.SINGLE)},
    )


class ExceptionalOccurrenceMode(DiscreteOccurrenceMode):
    __tablename__ = None
    __mapper_args__ = {
        "polymorphic_identity": OccurrenceKind.EXCEPTIONAL,
        "polymorphic_load": "inline",
    }

    # occurrence_id
    # exception_id

    ResponseSchema = MappedModel.create(
        bases=[DiscreteOccurrenceMode.ResponseSchema],
        extra_fields={
            "kind": (Literal[OccurrenceKind.EXCEPTIONAL], OccurrenceKind.EXCEPTIONAL)
        },
    )


class RepeatingOccurrenceMode(OccurrenceMode):
    __tablename__ = None
    __mapper_args__ = {
        "polymorphic_abstract": True,
    }

    is_finite: Mapped[bool] = mapped_column(default=False, nullable=True)

    @property
    def active_period_days(self) -> int | None:
        return self.duration.days if self.is_finite else None

    InnerInputSchema = MappedModel.create(
        bases=[OccurrenceMode.InnerInputSchema],
        columns=[is_finite],
    )
    ResponseSchema = MappedModel.create(
        bases=[OccurrenceMode.ResponseSchema],
        properties=[active_period_days],
    )

    @classmethod
    def iter_in_range_conditions(
        cls,
        happens_after_utc: datetime,
        happens_before_utc: datetime,
    ) -> Iterator[SQLColumnExpression[bool]]:
        yield from super().iter_in_range_conditions(
            happens_after_utc=happens_after_utc,
            happens_before_utc=happens_before_utc,
        )
        yield or_(cls.is_finite.is_(False), cls.ends_at_utc >= happens_after_utc)

    def iter_daily_event_instances_in_range(
        self,
        happens_after_utc: datetime,
        happens_before_utc: datetime,
    ) -> Iterator[tuple[int, datetime]]:
        if self.starts_at_utc > happens_after_utc - self.event_instance_duration:
            current_starts_at_utc = self.starts_at_utc
        else:
            current_starts_at_utc = datetime.combine(
                (happens_after_utc + timedelta(days=1)).date(),
                self.starts_at_utc.time(),
            )

        starting_event_instance_id: int = (
            current_starts_at_utc - self.starts_at_utc
        ).days

        if self.is_finite and self.ends_at_utc < happens_before_utc:
            starts_at_utc_upper_bound = self.ends_at_utc
        else:
            starts_at_utc_upper_bound = happens_before_utc

        while current_starts_at_utc < starts_at_utc_upper_bound:
            yield starting_event_instance_id, current_starts_at_utc
            current_starts_at_utc += timedelta(days=1)
            starting_event_instance_id += 1


class DailyOccurrenceMode(RepeatingOccurrenceMode):
    __tablename__ = None
    __mapper_args__ = {
        "polymorphic_identity": OccurrenceKind.DAILY,
        "polymorphic_load": "inline",
    }

    ResponseSchema = MappedModel.create(
        bases=[RepeatingOccurrenceMode.ResponseSchema],
        extra_fields={"kind": (Literal[OccurrenceKind.DAILY], OccurrenceKind.DAILY)},
    )

    def iter_event_instances_in_range(
        self,
        happens_after_utc: datetime,
        happens_before_utc: datetime,
    ) -> Iterator[tuple[int, datetime]]:
        yield from self.iter_daily_event_instances_in_range(
            happens_after_utc=happens_after_utc,
            happens_before_utc=happens_before_utc,
        )


class BitMaskedRepeatingOccurrenceMode(RepeatingOccurrenceMode):
    __tablename__ = None
    __mapper_args__ = {
        "polymorphic_abstract": True,
    }

    bitmask_size: ClassVar[int]

    @classmethod
    def get_combined_bitmask_field(cls) -> InstrumentedAttribute[int]:
        raise NotImplementedError

    def get_starting_bitmask(self) -> TimestampRelativeBitmask:
        raise NotImplementedError

    @classmethod
    def iter_in_range_conditions(
        cls,
        happens_after_utc: datetime,
        happens_before_utc: datetime,
    ) -> Iterator[SQLColumnExpression[bool]]:
        yield from super().iter_in_range_conditions(
            happens_after_utc=happens_after_utc,
            happens_before_utc=happens_before_utc,
        )

        if happens_before_utc - happens_after_utc < timedelta(
            days=cls.bitmask_size - 1
        ):
            interval_bitmask = construct_continuous_bitmask(
                left=happens_after_utc.weekday(),
                right=happens_before_utc.weekday(),
                size=cls.bitmask_size,
            )
            yield cls.get_combined_bitmask_field().bitwise_and(interval_bitmask) != 0

    def iter_event_instances_in_range(
        self,
        happens_after_utc: datetime,
        happens_before_utc: datetime,
    ) -> Iterator[tuple[int, datetime]]:
        starting_bitmask = self.get_starting_bitmask()

        yield from (
            (event_instance_id, current_starts_at)
            for (
                event_instance_id,
                current_starts_at,
            ) in self.iter_daily_event_instances_in_range(
                happens_after_utc=happens_after_utc,
                happens_before_utc=happens_before_utc,
            )
            if starting_bitmask.check_if_timestamp_matches(current_starts_at)
        )


class WeeklyOccurrenceMode(BitMaskedRepeatingOccurrenceMode):
    __tablename__ = None
    __mapper_args__ = {
        "polymorphic_identity": OccurrenceKind.WEEKLY,
        "polymorphic_load": "inline",
    }

    bitmask_size = 7

    weekly_starting_bitmask: Mapped[int] = mapped_column(
        PSQLBitmask(bitmask_size), nullable=True
    )
    weekly_combined_bitmask: Mapped[int] = mapped_column(
        PSQLBitmask(bitmask_size), nullable=True
    )

    InnerInputSchema = MappedModel.create(
        bases=[BitMaskedRepeatingOccurrenceMode.InnerInputSchema],
        columns=[weekly_starting_bitmask, weekly_combined_bitmask],
    )
    ResponseSchema = MappedModel.create(
        bases=[BitMaskedRepeatingOccurrenceMode.ResponseSchema],
        columns=[weekly_starting_bitmask],
        extra_fields={"kind": (Literal[OccurrenceKind.WEEKLY], OccurrenceKind.WEEKLY)},
    )

    @classmethod
    def get_combined_bitmask_field(cls) -> InstrumentedAttribute[int]:
        return cls.weekly_combined_bitmask

    def get_starting_bitmask(self) -> WeeklyBitmask:
        return WeeklyBitmask(self.weekly_starting_bitmask)


ConcreteOccurrenceModeClasses: tuple[type[OccurrenceMode], ...] = (
    SingleOccurrenceMode,
    ExceptionalOccurrenceMode,
    DailyOccurrenceMode,
    WeeklyOccurrenceMode,
)

# `polymorphic_load: inline` doesn't work in complex queries for some reason
OccurrenceModePolymorphic = with_polymorphic(
    OccurrenceMode,
    ConcreteOccurrenceModeClasses,
)

OccurrenceModeResponseSchema = Annotated[
    SingleOccurrenceMode.ResponseSchema
    | ExceptionalOccurrenceMode.ResponseSchema
    | DailyOccurrenceMode.ResponseSchema
    | WeeklyOccurrenceMode.ResponseSchema,
    Field(discriminator="kind"),
]


class BaseOccurrenceModeInputSchema(BaseModel):
    db_class: ClassVar[type[Base]]

    max_event_length: ClassVar[timedelta] = timedelta(hours=12)
    max_timedelta_to_the_past: ClassVar[timedelta] = timedelta(days=370)
    max_timedelta_to_the_future: ClassVar[timedelta] = timedelta(days=370)

    starts_at: AwareDatetime = Field(exclude=True)
    duration_seconds: int = Field(gt=0, le=max_event_length.seconds, exclude=True)

    @model_validator(mode="after")
    def validate_starts_at_range(self) -> Self:
        timedelta_from_now_to_start: timedelta = self.starts_at - datetime_utc_now()
        if timedelta_from_now_to_start < -self.max_timedelta_to_the_past:
            raise ValueError("start is too far in the past")
        if timedelta_from_now_to_start > self.max_timedelta_to_the_future:
            raise ValueError("start is too far in the future")
        return self

    @computed_field
    @property
    def starts_at_utc(self) -> datetime:
        return self.starts_at.astimezone(tz=timezone.utc).replace(tzinfo=None)

    @computed_field
    @property
    def ends_at_utc(self) -> datetime:
        return self.starts_at_utc + timedelta(seconds=self.duration_seconds)


class BaseDiscreteOccurrenceModeInputSchema(BaseOccurrenceModeInputSchema):
    pass


class SingleOccurrenceModeInputSchema(BaseDiscreteOccurrenceModeInputSchema):
    db_class: ClassVar[type[Base]] = SingleOccurrenceMode

    kind: Literal[OccurrenceKind.SINGLE] = OccurrenceKind.SINGLE


class BaseRepeatingOccurrenceModeInputSchema(BaseOccurrenceModeInputSchema):
    active_period_days: int | None = Field(None, gt=0, exclude=True)

    @model_validator(mode="after")
    def validate_active_period_does_not_end_too_far_in_the_future(self) -> Self:
        if self.active_period_days is None:
            return self
        active_period_ends_at: datetime = self.starts_at + timedelta(
            days=self.active_period_days
        )
        if (
            active_period_ends_at - datetime_utc_now()
            <= self.max_timedelta_to_the_future
        ):
            return self
        raise ValueError("active period's end is too far in the future")

    @computed_field
    @property
    def ends_at_utc(self) -> datetime:
        result = super().ends_at_utc
        if self.active_period_days is None:
            return result
        return result + timedelta(days=self.active_period_days)

    @computed_field
    @property
    def is_finite(self) -> bool:
        return self.active_period_days is not None


class DailyOccurrenceModeInputSchema(BaseRepeatingOccurrenceModeInputSchema):
    db_class: ClassVar[type[Base]] = DailyOccurrenceMode

    kind: Literal[OccurrenceKind.DAILY] = OccurrenceKind.DAILY


class BaseBitMaskedOccurrenceModeInputSchema[BitmaskType: TimestampRelativeBitmask](
    BaseRepeatingOccurrenceModeInputSchema
):
    @property
    @abstractmethod
    def bitmask(self) -> BitmaskType:
        raise NotImplementedError

    @property
    def starting_bitmask(self) -> BitmaskType:
        return self.bitmask.replace_origin(
            old_origin=self.starts_at,
            new_origin=self.starts_at_utc,
        )

    @property
    def ending_bitmask(self) -> BitmaskType:
        return self.bitmask.replace_origin(
            old_origin=self.starts_at,
            new_origin=self.starts_at_utc + timedelta(seconds=self.duration_seconds),
        )

    @property
    def combined_bitmask_value(self) -> int:
        return self.starting_bitmask.value | self.ending_bitmask.value


class WeeklyOccurrenceModeInputSchema(
    BaseBitMaskedOccurrenceModeInputSchema[WeeklyBitmask]
):
    db_class: ClassVar[type[Base]] = WeeklyOccurrenceMode

    kind: Literal[OccurrenceKind.WEEKLY] = OccurrenceKind.WEEKLY

    weekly_bitmask: int = Field(gt=0, lt=2**7 - 1, exclude=True)

    @property
    def bitmask(self) -> WeeklyBitmask:
        return WeeklyBitmask(self.weekly_bitmask)

    @computed_field
    @property
    def weekly_starting_bitmask(self) -> int:
        return self.starting_bitmask.value

    @computed_field
    @property
    def weekly_combined_bitmask(self) -> int:
        return self.combined_bitmask_value


OccurrenceModeInputSchema = Annotated[
    SingleOccurrenceModeInputSchema
    | DailyOccurrenceModeInputSchema
    | WeeklyOccurrenceModeInputSchema,
    Field(discriminator="kind"),
]
