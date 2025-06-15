from collections.abc import Sequence
from datetime import datetime
from typing import Annotated, Self

from pydantic import AwareDatetime, Field
from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import DateTime, String, and_, select
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base
from app.common.sqlalchemy_ext import db


class Event(Base):
    __tablename__ = "scheduler_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(String(1000), default=None)

    NameType = Annotated[str, Field(min_length=1, max_length=100)]
    DescriptionType = Annotated[str | None, Field(min_length=1, max_length=1000)]

    InputSchema = MappedModel.create(
        columns=[
            (starts_at, AwareDatetime),
            (ends_at, AwareDatetime),
            (name, NameType),
            (description, DescriptionType),
        ],
    )
    ResponseSchema = InputSchema.extend([id])

    @classmethod
    async def find_all_events_in_time_frame(
        cls, *, happens_after: datetime, happens_before: datetime
    ) -> Sequence[Self]:
        stmt = (
            select(cls)
            .where(and_(cls.starts_at < happens_before, cls.ends_at > happens_after))
            .order_by(cls.starts_at.desc())
        )
        return await db.get_all(stmt)
