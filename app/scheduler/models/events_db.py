from collections.abc import Sequence
from enum import StrEnum, auto
from typing import Annotated, Literal, Self

from pydantic import Field
from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import Enum, String, select
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base
from app.common.sqlalchemy_ext import db


class EventKind(StrEnum):
    CLASSROOM = auto()


class Event(Base):
    __tablename__: str | None = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
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
            (name, NameType),
            (description, DescriptionType),
        ],
    )
    PatchSchema = InputSchema.as_patch()
    ResponseSchema = InputSchema.extend(columns=[id])

    @classmethod
    async def find_all_by_ids(cls, event_ids: list[int]) -> Sequence[Self]:
        return await db.get_all(select(cls).filter(cls.id.in_(event_ids)))


class ClassroomEvent(Event):
    __tablename__ = None

    __mapper_args__ = {
        "polymorphic_identity": EventKind.CLASSROOM,
        "polymorphic_load": "inline",
    }

    classroom_id: Mapped[int] = mapped_column(nullable=True)

    ResponseSchema = MappedModel.create(
        bases=[Event.ResponseSchema],
        columns=[classroom_id],
        extra_fields={"kind": (Literal[EventKind.CLASSROOM], EventKind.CLASSROOM)},
    )
