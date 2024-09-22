from collections.abc import Sequence
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Self

from pydantic import AwareDatetime
from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import (
    ColumnElement,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    and_,
    select,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base
from app.common.sqlalchemy_ext import db
from app.communities.models.task_channels_db import TaskChannel


class TaskKind(StrEnum):
    TASK = "task"
    TEST = "test"


class TaskOrderingType(StrEnum):
    CREATED_AT = "created_at"
    OPENING_AT = "opening_at"
    CLOSING_AT = "closing_at"


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    title: Mapped[str] = mapped_column(String(100))
    kind: Mapped[TaskKind] = mapped_column(Enum(TaskKind))
    opening_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    closing_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    author_id: Mapped[int] = mapped_column()
    channel_id: Mapped[int] = mapped_column(
        ForeignKey(TaskChannel.id, ondelete="CASCADE")
    )

    __table_args__ = (
        Index("hash_index_tasks_channel_id", channel_id, postgresql_using="hash"),
    )

    ORDER_BY_FIELD: dict[TaskOrderingType, ColumnElement[Any]] = {
        TaskOrderingType.CREATED_AT: created_at.desc(),
        TaskOrderingType.OPENING_AT: opening_at.desc(),
        TaskOrderingType.CLOSING_AT: closing_at.desc(),
    }

    InputSchema = MappedModel.create(
        columns=[  # noqa: WPS317  # linter bug
            title,
            kind,
            (opening_at, AwareDatetime),
            (closing_at, AwareDatetime),
            author_id,
        ],
    )
    PatchSchema = InputSchema.as_patch()
    ResponseSchema = InputSchema.extend(columns=[id, created_at])

    @property
    def is_active(self) -> bool:
        return self.opening_at <= datetime.now(timezone.utc) < self.closing_at

    @classmethod
    async def find_paginated_by_filter(
        cls,
        channel_id: int,
        offset: int,
        limit: int,
        is_only_active: bool,
        ordering_type: TaskOrderingType,
        kind: TaskKind | None,
    ) -> Sequence[Self]:
        stmt = select(cls).filter_by(channel_id=channel_id)

        if is_only_active:
            current_utc_time = datetime.now(timezone.utc)
            stmt = stmt.filter(
                and_(
                    cls.opening_at <= current_utc_time,
                    cls.closing_at > current_utc_time,
                )
            )

        if kind is not None:
            stmt = stmt.filter(cls.kind == kind)

        stmt = stmt.order_by(cls.ORDER_BY_FIELD[ordering_type])

        return await db.get_paginated(stmt, offset, limit)
