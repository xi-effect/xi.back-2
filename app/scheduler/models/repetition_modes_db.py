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
    computed_field,
    model_validator,
    TypeAdapter,
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
    relationship,
)

from app.common.config import Base
from app.common.utils.datetime import datetime_utc_now
from app.scheduler.config import (
    MAX_EVENT_INSTANCE_DURATION,
    MAX_TIMEDELTA_TO_THE_FUTURE,
    MAX_TIMEDELTA_TO_THE_PAST,
    MIN_EVENT_INSTANCE_DURATION,
)
from app.scheduler.models.events_db import Event
from app.scheduler.utils.bitmasks import (
    PSQLBitmask,
    TimestampRelativeBitmask,
    WeeklyBitmask,
)


class RepetitionKind(StrEnum):
    DAILY = auto()
    WEEKLY = auto()


class RepetitionMode(Base):
    __tablename__: str | None = "repetition_modes"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    event_id: Mapped[int] = mapped_column(
        ForeignKey(Event.id, ondelete="CASCADE"),
        index=True,
    )
    event: Mapped[Event] = relationship(lazy="joined")

    kind: Mapped[RepetitionKind] = mapped_column(Enum(RepetitionKind))

    starts_at: Mapped[datetime] = mapped_column(TIMESTAMP(precision=0, timezone=True))
    ends_at: Mapped[datetime] = mapped_column(TIMESTAMP(precision=0, timezone=True))
    is_finite: Mapped[bool] = mapped_column(default=False, nullable=True)

    __mapper_args__ = {
        "polymorphic_on": kind,
        "polymorphic_abstract": True,
        "with_polymorphic": "*",  # `polymorphic_load: inline` doesn't work in complex queries for some reason
    }

    __table_args__ = (
        Index("index_repetition_modes_kind_and_interval", kind, starts_at, ends_at),
    )

    @property
    def duration(self) -> timedelta:
        return self.ends_at - self.starts_at

    @property
    def duration_seconds(self) -> int:
        return self.duration.seconds

    @property
    def event_instance_duration(self) -> timedelta:
        return timedelta(seconds=self.duration_seconds)

    @property
    def active_period_days(self) -> int | None:
        return self.duration.days if self.is_finite else None

    ResponseSchema = MappedModel.create(
        columns=[id, event_id, starts_at],
        properties=[duration_seconds, active_period_days],
    )

    @classmethod
    def iter_in_range_conditions(
        cls,
        happens_after: datetime,
        happens_before: datetime,
    ) -> Iterator[SQLColumnExpression[bool]]:
        yield cls.kind == cls.__mapper__.polymorphic_identity
        yield cls.starts_at <= happens_before
        yield or_(cls.is_finite.is_(False), cls.ends_at > happens_after)

    def calculate_event_instance_starts_at_for_index(
        self,
        instance_index: int,
    ) -> datetime:
        raise NotImplementedError

    def calculate_event_instance_index_for_starts_at(
        self,
        event_instance_starts_at: datetime,
    ) -> int:
        raise NotImplementedError

    def get_starts_at_bounds_in_range(
        self,
        happens_after: datetime,
        happens_before: datetime,
    ) -> tuple[datetime, datetime]:
        if self.starts_at > happens_after - self.event_instance_duration:
            starts_at_lower_bound = self.starts_at
        else:
            starts_at_lower_bound = datetime.combine(
                happens_after.date(),
                self.starts_at.time(),
                self.starts_at.tzinfo,
            )
            if (
                (happens_after - self.starts_at) % timedelta(days=1)
            ) >= self.event_instance_duration:
                # TODO use bitmask's unit instead of `days=1`
                #   or just implement "skipping" the first starts at
                starts_at_lower_bound += timedelta(days=1)

        if self.is_finite and self.ends_at < happens_before:
            starts_at_upper_bound = self.ends_at
        else:
            starts_at_upper_bound = happens_before

        return starts_at_lower_bound, starts_at_upper_bound

    def iter_event_instances_in_range(
        self,
        happens_after: datetime,
        happens_before: datetime,
    ) -> Iterator[tuple[int, datetime]]:
        """This method assumes, that the repetition mode is inside the range (checked on query level)"""
        raise NotImplementedError


class DailyRepetitionMode(RepetitionMode):
    __tablename__ = None
    __mapper_args__ = {
        "polymorphic_identity": RepetitionKind.DAILY,
        "polymorphic_load": "inline",
    }

    ResponseSchema = MappedModel.create(
        bases=[RepetitionMode.ResponseSchema],
        extra_fields={"kind": (Literal[RepetitionKind.DAILY], RepetitionKind.DAILY)},
    )

    def calculate_event_instance_starts_at_for_index(
        self,
        instance_index: int,
    ) -> datetime:
        return self.starts_at + timedelta(days=instance_index)

    def calculate_event_instance_index_for_starts_at(
        self,
        event_instance_starts_at: datetime,
    ) -> int:
        return (event_instance_starts_at - self.starts_at).days

    def iter_event_instances_in_range(
        self,
        happens_after: datetime,
        happens_before: datetime,
    ) -> Iterator[tuple[int, datetime]]:
        current_starts_at, starts_at_upper_bound = self.get_starts_at_bounds_in_range(
            happens_after=happens_after,
            happens_before=happens_before,
        )
        current_event_instance_index: int = (
            self.calculate_event_instance_index_for_starts_at(
                event_instance_starts_at=current_starts_at
            )
        )
        while current_starts_at < starts_at_upper_bound:
            yield current_event_instance_index, current_starts_at
            current_starts_at += timedelta(days=1)
            current_event_instance_index += 1


class BitMaskedRepeatingRepetitionMode(RepetitionMode):
    __tablename__ = None
    __mapper_args__ = {
        "polymorphic_abstract": True,
    }

    bitmask_type: ClassVar[type[TimestampRelativeBitmask]]

    @classmethod
    def get_combined_bitmask_field(cls) -> InstrumentedAttribute[int]:
        raise NotImplementedError

    @property
    def starting_bitmask(self) -> TimestampRelativeBitmask:
        raise NotImplementedError

    @classmethod
    def iter_in_range_conditions(
        cls,
        happens_after: datetime,
        happens_before: datetime,
    ) -> Iterator[SQLColumnExpression[bool]]:
        yield from super().iter_in_range_conditions(
            happens_after=happens_after,
            happens_before=happens_before,
        )

        if (
            happens_before - happens_after
            < (cls.bitmask_type.size - 1) * cls.bitmask_type.unit_duration
        ):
            interval_bitmask = cls.bitmask_type.build_continuous(
                start_timestamp=happens_after.astimezone(timezone.utc),
                end_timestamp=happens_before.astimezone(timezone.utc),
            )
            yield cls.get_combined_bitmask_field().bitwise_and(
                interval_bitmask.value
            ) != 0

    def calculate_event_instance_starts_at_for_index(
        self,
        instance_index: int,
    ) -> datetime:
        offset_in_cycles = instance_index // self.starting_bitmask.value.bit_count()

        rotated_bitmask_value: int = self.starting_bitmask.rotate(
            source_position=self.starting_bitmask.position_from_timestamp(
                self.starts_at.astimezone(timezone.utc)
            ),
            target_position=-1,
        ).value

        required_bit_count: int = (
            instance_index % self.starting_bitmask.value.bit_count()
        )
        offset_in_units: int = 0
        while required_bit_count > 0:
            if rotated_bitmask_value & 1:
                required_bit_count -= 1
            rotated_bitmask_value >>= 1
            offset_in_units += 1

        return (
            self.starts_at
            + offset_in_cycles * self.starting_bitmask.get_cycle_duration()
            + offset_in_units * self.starting_bitmask.unit_duration
        )

    def calculate_event_instance_index_for_starts_at(
        self,
        event_instance_starts_at: datetime,
    ) -> int:
        repetition_mode_cycle_offset: int = (
            self.starting_bitmask.calculate_cycle_offset_for_timestamp(
                timestamp=self.starts_at.astimezone(timezone.utc),
            )
        )
        event_instance_cycle_offset: int = (
            self.starting_bitmask.calculate_cycle_offset_for_timestamp(
                timestamp=event_instance_starts_at.astimezone(timezone.utc),
            )
        )
        return (
            (event_instance_starts_at - self.starts_at)
            // self.bitmask_type.get_cycle_duration()
            * self.starting_bitmask.value.bit_count()
        ) + (
            (event_instance_cycle_offset - repetition_mode_cycle_offset)
            % self.starting_bitmask.value.bit_count()
        )

    def iter_event_instances_in_range(
        self,
        happens_after: datetime,
        happens_before: datetime,
    ) -> Iterator[tuple[int, datetime]]:
        current_starts_at, starts_at_upper_bound = self.get_starts_at_bounds_in_range(
            happens_after=happens_after,
            happens_before=happens_before,
        )

        current_event_instance_index: int | None = None
        while current_starts_at < starts_at_upper_bound:
            if self.starting_bitmask.check_if_timestamp_matches(current_starts_at):
                if current_event_instance_index is None:
                    current_event_instance_index = (
                        self.calculate_event_instance_index_for_starts_at(
                            current_starts_at
                        )
                    )
                yield current_event_instance_index, current_starts_at
                current_event_instance_index += 1
            current_starts_at += self.starting_bitmask.unit_duration


class WeeklyRepetitionMode(BitMaskedRepeatingRepetitionMode):
    __tablename__ = None
    __mapper_args__ = {
        "polymorphic_identity": RepetitionKind.WEEKLY,
        "polymorphic_load": "inline",
    }

    bitmask_type = WeeklyBitmask
    bitmask_size = WeeklyBitmask.size

    weekly_starting_bitmask: Mapped[int] = mapped_column(
        PSQLBitmask(bitmask_size), nullable=True
    )
    weekly_combined_bitmask: Mapped[int] = mapped_column(
        PSQLBitmask(bitmask_size), nullable=True
    )

    ResponseSchema = MappedModel.create(
        bases=[BitMaskedRepeatingRepetitionMode.ResponseSchema],
        columns=[weekly_starting_bitmask],
        extra_fields={"kind": (Literal[RepetitionKind.WEEKLY], RepetitionKind.WEEKLY)},
    )

    @classmethod
    def get_combined_bitmask_field(cls) -> InstrumentedAttribute[int]:
        return cls.weekly_combined_bitmask

    @property
    def starting_bitmask(self) -> WeeklyBitmask:
        return WeeklyBitmask(self.weekly_starting_bitmask)


ConcreteRepetitionModeClasses: tuple[type[RepetitionMode], ...] = (
    DailyRepetitionMode,
    WeeklyRepetitionMode,
)


class BaseRepetitionModeInputSchema(BaseModel):
    db_class: ClassVar[type[Base]]

    starts_at: AwareDatetime
    duration_seconds: int = Field(
        gt=MIN_EVENT_INSTANCE_DURATION.seconds,
        le=MAX_EVENT_INSTANCE_DURATION.seconds,
        exclude=True,
    )
    active_period_days: int | None = Field(None, gt=0, exclude=True)

    @model_validator(mode="after")
    def validate_starts_at_range(self) -> Self:
        timedelta_from_now_to_start: timedelta = self.starts_at - datetime_utc_now()
        if timedelta_from_now_to_start < MAX_TIMEDELTA_TO_THE_PAST:
            raise ValueError("start is too far in the past")
        if timedelta_from_now_to_start > MAX_TIMEDELTA_TO_THE_FUTURE:
            raise ValueError("start is too far in the future")
        return self

    @model_validator(mode="after")
    def validate_active_period_does_not_end_too_far_in_the_future(self) -> Self:
        if self.active_period_days is None:
            return self
        active_period_ends_at: datetime = self.starts_at + timedelta(
            days=self.active_period_days
        )
        if active_period_ends_at - datetime_utc_now() <= MAX_TIMEDELTA_TO_THE_FUTURE:
            return self
        raise ValueError("active period's end is too far in the future")

    @property
    def starts_at_utc(self) -> datetime:
        return self.starts_at.astimezone(timezone.utc)

    @computed_field
    @property
    def ends_at(self) -> datetime:
        return self.starts_at + timedelta(
            seconds=self.duration_seconds,
            days=self.active_period_days or 0,
        )

    @computed_field
    @property
    def is_finite(self) -> bool:
        return self.active_period_days is not None


class DailyRepetitionModeInputSchema(BaseRepetitionModeInputSchema):
    db_class = DailyRepetitionMode

    kind: Literal[RepetitionKind.DAILY] = RepetitionKind.DAILY


class BaseBitMaskedRepetitionModeInputSchema[BitmaskType: TimestampRelativeBitmask](
    BaseRepetitionModeInputSchema
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
    BaseBitMaskedRepetitionModeInputSchema[WeeklyBitmask]
):
    db_class = WeeklyRepetitionMode

    kind: Literal[RepetitionKind.WEEKLY] = RepetitionKind.WEEKLY

    weekly_bitmask: int = Field(
        gt=0,
        lt=2**WeeklyRepetitionMode.bitmask_size - 1,
        exclude=True,
    )

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


RepetitionModeInputSchema = Annotated[
    DailyRepetitionModeInputSchema | WeeklyOccurrenceModeInputSchema,
    Field(discriminator="kind"),
]

RepetitionModeResponseSchema = Annotated[
    DailyRepetitionMode.ResponseSchema | WeeklyRepetitionMode.ResponseSchema,
    Field(discriminator="kind"),
]

REPETITION_MODE_TYPE_ADAPTER: TypeAdapter[RepetitionModeResponseSchema] = TypeAdapter(
    RepetitionModeResponseSchema
)
