from datetime import datetime, timedelta
from enum import StrEnum, auto
from typing import Annotated, Literal
from uuid import UUID, uuid4

from pydantic import AwareDatetime, BaseModel, Field, computed_field
from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, and_
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base
from app.scheduler.config import (
    MAX_EVENT_INSTANCE_DURATION,
    MIN_EVENT_INSTANCE_DURATION,
)
from app.scheduler.models.events_db import Event
from app.scheduler.models.repetition_modes_db import RepetitionMode


class EventInstanceResponseSchemaKind(StrEnum):
    SOLE = auto()
    REPEATED_PERSISTENT = auto()
    REPEATED_VIRTUAL = auto()


class BaseEventInstanceResponseSchema(BaseModel):
    event_id: int
    classroom_id: int  # TODO: ClassroomEvent-specific

    starts_at: AwareDatetime
    ends_at: AwareDatetime

    name: str
    description: str | None = None


class PersistedEventInstanceDataMixin(BaseModel):
    id: UUID
    cancelled_at: AwareDatetime | None = None

    # TODO "meta"
    # TODO could just add name & description from Event as proxies


class SoleEventInstanceResponseSchema(
    BaseEventInstanceResponseSchema,
    PersistedEventInstanceDataMixin,
):
    kind: Literal[EventInstanceResponseSchemaKind.SOLE] = (
        EventInstanceResponseSchemaKind.SOLE
    )


class BaseRepeatedEventInstanceResponseSchema(BaseEventInstanceResponseSchema):
    repetition_mode_id: UUID
    instance_index: int


class PersistedRepeatedEventInstanceResponseSchema(
    BaseRepeatedEventInstanceResponseSchema,
    PersistedEventInstanceDataMixin,
):
    kind: Literal[EventInstanceResponseSchemaKind.REPEATED_PERSISTENT] = (
        EventInstanceResponseSchemaKind.REPEATED_PERSISTENT
    )


class VirtualRepeatedEventInstanceResponseSchema(
    BaseRepeatedEventInstanceResponseSchema,
):
    kind: Literal[EventInstanceResponseSchemaKind.REPEATED_VIRTUAL] = (
        EventInstanceResponseSchemaKind.REPEATED_VIRTUAL
    )


EventInstanceResponseSchema = Annotated[
    SoleEventInstanceResponseSchema
    | PersistedRepeatedEventInstanceResponseSchema
    | VirtualRepeatedEventInstanceResponseSchema,
    Field(discriminator="kind"),
]


class EventInstanceKind(StrEnum):
    SOLE = auto()
    REPEATED = auto()


class EventInstance(Base):
    __tablename__: str | None = "event_instances"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    kind: Mapped[EventInstanceKind] = mapped_column(Enum(EventInstanceKind))

    event_id: Mapped[int] = mapped_column(
        # In RepeatedEventInstance this is denormalization,
        # but it is useful for faster and more consistent queries
        # Also `ForeignKey` can't generate two different constraints for subclasses
        ForeignKey(Event.id, ondelete="CASCADE"),
        use_existing_column=True,
    )

    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=None,
    )
    # TODO "meta"

    __mapper_args__ = {
        "polymorphic_on": kind,
        "polymorphic_abstract": True,
    }


class SoleEventInstance(EventInstance):
    __tablename__ = None

    __mapper_args__ = {
        "polymorphic_identity": EventInstanceKind.SOLE,
        "polymorphic_load": "inline",
    }

    starts_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(precision=0, timezone=True),
        nullable=True,
    )
    ends_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(precision=0, timezone=True),
        nullable=True,
    )


# declared outside the class, because STI doesn't support indexes on child classes
Index(
    "unique_index_sole_event_instances_event_id",
    SoleEventInstance.event_id,
    postgresql_where=EventInstance.kind == EventInstanceKind.SOLE,
    unique=True,
)
Index(
    "index_sole_event_instance_interval",
    SoleEventInstance.starts_at,
    SoleEventInstance.ends_at,
    postgresql_where=EventInstance.kind == EventInstanceKind.SOLE,
)


class RepeatedEventInstance(EventInstance):
    __tablename__ = None

    __mapper_args__ = {
        "polymorphic_identity": EventInstanceKind.REPEATED,
        "polymorphic_load": "inline",
    }

    repetition_mode_id: Mapped[UUID] = mapped_column(
        ForeignKey(RepetitionMode.id, ondelete="CASCADE"),
        nullable=True,
    )
    instance_index: Mapped[int] = mapped_column(nullable=True)

    starts_at_override: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(precision=0, timezone=True),
        default=None,
    )
    ends_at_override: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(precision=0, timezone=True),
        default=None,
    )
    # TODO make sure that either both or neither are specified

    name_override: Mapped[str | None] = mapped_column(
        String(100),
        default=None,
    )
    description_override: Mapped[str | None] = mapped_column(
        String(1000),
        default=None,
    )


# declared outside the class, because STI doesn't support indexes on child classes
Index(
    "index_repeated_event_instances_ids",
    RepeatedEventInstance.repetition_mode_id,
    RepeatedEventInstance.instance_index,
    postgresql_where=EventInstance.kind == EventInstanceKind.REPEATED,
)
Index(
    "index_repeated_event_instance_interval_override",
    RepeatedEventInstance.starts_at_override,
    RepeatedEventInstance.ends_at_override,
    postgresql_where=and_(
        EventInstance.kind == EventInstanceKind.REPEATED,
        RepeatedEventInstance.starts_at_override.is_not(None),
        RepeatedEventInstance.ends_at_override.is_not(None),
    ),
)


AnyEventInstance = SoleEventInstance | RepeatedEventInstance


class SoleEventInstanceInputSchema(BaseModel):
    starts_at: AwareDatetime
    duration_seconds: int = Field(
        gt=MIN_EVENT_INSTANCE_DURATION.seconds,
        le=MAX_EVENT_INSTANCE_DURATION.seconds,
        exclude=True,
    )

    @computed_field
    @property
    def ends_at(self) -> datetime:
        return self.starts_at + timedelta(seconds=self.duration_seconds)
