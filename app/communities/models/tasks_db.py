from collections.abc import Sequence
from datetime import datetime
from enum import Enum
from typing import Self

from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, Index, String, select
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.config import Base
from app.common.sqlalchemy_ext import db
from app.communities.models.communities_db import Community


class TaskOrdering(Enum):
    CLOSING_DATE = "closing_date"
    OPENING_DATE = "opening_date"
    CREATION_DATE = "creation_date"


class TaskType(Enum):
    TEST = "test"
    WRITING = "exercise"


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    task_type: Mapped[TaskType] = mapped_column(SQLEnum(TaskType))
    creation_date: Mapped[datetime] = mapped_column(default=datetime.now)
    opening_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    closing_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    community_id: Mapped[int] = mapped_column(
        ForeignKey(Community.id, ondelete="CASCADE"),
    )
    community = relationship("Community")

    __table_args__ = (
        Index("hash_index_tasks_community_id", community_id, postgresql_using="hash"),
    )

    InputSchema = MappedModel.create(
        columns=[name, task_type, opening_date, closing_date]
    )
    PatchSchema = InputSchema.as_patch()
    ResponseSchema = MappedModel.create(
        columns=[
            id,
            name,
            task_type,
            creation_date,
            opening_date,
            closing_date,
        ]
    )
    DeleteSchema = MappedModel.create(columns=[id, community_id])

    @classmethod
    async def get_paginated(  # noqa: WPS211
        cls,
        community_id: int,
        offset: int,
        limit: int,
        is_only_active: bool,
        ordering: TaskOrdering,
    ) -> Sequence[Self]:
        stmt = select(cls).filter_by(community_id=community_id)

        if is_only_active:
            stmt = stmt.where(cls.opening_date <= cls.closing_date)

        if ordering is TaskOrdering.CLOSING_DATE:
            stmt = stmt.order_by(cls.closing_date)
        if ordering is TaskOrdering.OPENING_DATE:
            stmt = stmt.order_by(cls.opening_date)
        if ordering is TaskOrdering.CREATION_DATE:
            stmt = stmt.order_by(cls.creation_date)

        return await db.get_paginated(stmt, offset, limit)
