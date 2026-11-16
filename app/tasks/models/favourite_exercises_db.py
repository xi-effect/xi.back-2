from collections.abc import Sequence
from datetime import datetime
from typing import Self
from uuid import UUID

from pydantic import AwareDatetime
from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import DateTime, Index, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base
from app.common.sqlalchemy_ext import db
from app.common.utils.datetime import datetime_utc_now


class FavouriteExercise(Base):
    __tablename__ = "favourite_exercises"

    user_id: Mapped[int] = mapped_column(primary_key=True)
    exercise_id: Mapped[UUID] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime_utc_now
    )

    __table_args__ = (
        Index(
            "index_favourite_exercise_user_id_created_at_exercise_id",
            user_id,
            created_at,
            exercise_id,
        ),
    )

    ResponseSchema = MappedModel.create(
        columns=[exercise_id, (created_at, AwareDatetime)]
    )

    @classmethod
    async def find_paginated_by_user_id(
        cls,
        user_id: int,
        created_before: datetime | None,
        limit: int,
    ) -> Sequence[Self]:
        stmt = select(cls).filter_by(user_id=user_id)
        if created_before is not None:
            stmt = stmt.filter(cls.created_at < created_before)
        return await db.get_all(
            stmt.order_by(cls.created_at.desc(), cls.exercise_id.desc()).limit(limit)
        )

    @classmethod
    async def upsert_by_ids(cls, user_id: int, exercise_id: UUID) -> None:
        await db.session.execute(
            insert(cls)
            .values(user_id=user_id, exercise_id=exercise_id)
            .on_conflict_do_nothing()
        )
