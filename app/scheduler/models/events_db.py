from collections.abc import Sequence
from datetime import datetime
from enum import StrEnum, auto
from typing import Annotated, Literal, Self

from pydantic import AwareDatetime, Field
from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import DateTime, Enum, String, and_, select
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base
from app.common.sqlalchemy_ext import db


class EventKind(StrEnum):
    CLASSROOM = auto()


class Event(Base):
    __tablename__: str | None = "scheduler_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(String(1000), default=None)

    kind: Mapped[EventKind] = mapped_column(Enum(EventKind))

    NameType = Annotated[str, Field(min_length=1, max_length=100)]
    DescriptionType = Annotated[str | None, Field(min_length=1, max_length=1000)]

    __mapper_args__ = {
        "polymorphic_on": kind,
        "polymorphic_abstract": True,
    }

    InputSchema = MappedModel.create(
        columns=[
            (starts_at, AwareDatetime),
            (ends_at, AwareDatetime),
            (name, NameType),
            (description, DescriptionType),
        ],
    )
    ResponseSchema = InputSchema.extend(columns=[id])


class ClassroomEvent(Event):
    __tablename__ = None

    __mapper_args__ = {
        "polymorphic_identity": EventKind.CLASSROOM,
        "polymorphic_load": "inline",
    }

    classroom_id: Mapped[int] = mapped_column(nullable=True)

    InputSchema = MappedModel.create(bases=[Event.InputSchema])
    ResponseSchema = MappedModel.create(
        bases=[Event.ResponseSchema],
        columns=[classroom_id],
        extra_fields={"kind": (Literal[EventKind.CLASSROOM], EventKind.CLASSROOM)},
    )

    @classmethod
    async def find_all_by_classroom_id_in_time_frame(
        cls,
        classroom_id: int,
        happens_after: datetime,
        happens_before: datetime,
    ) -> Sequence[Self]:
        return await db.get_all(
            select(cls)
            .filter_by(classroom_id=classroom_id)
            .filter(and_(cls.starts_at < happens_before, cls.ends_at > happens_after))
            .order_by(cls.starts_at.desc())
        )
