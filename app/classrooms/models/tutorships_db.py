from collections.abc import Sequence
from datetime import datetime
from typing import Self

from pydantic import AwareDatetime
from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import CheckConstraint, DateTime, select
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base
from app.common.sqlalchemy_ext import db
from app.common.utils.datetime import datetime_utc_now


class Tutorship(Base):
    __tablename__ = "tutorships"

    tutor_id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(primary_key=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime_utc_now
    )
    active_classroom_count: Mapped[int] = mapped_column(default=0)

    __table_args__ = (
        CheckConstraint(
            tutor_id != student_id,
            name="check_tutorship_tutor_id_ne_student_id",
        ),
    )

    ResponseSchema = MappedModel.create(
        columns=[(created_at, AwareDatetime), active_classroom_count]
    )
    TutorResponseSchema = ResponseSchema.extend(columns=[student_id])
    StudentResponseSchema = ResponseSchema.extend(columns=[tutor_id])

    @classmethod
    async def find_or_create(cls, tutor_id: int, student_id: int) -> Self:
        tutorship = await cls.find_first_by_kwargs(
            tutor_id=tutor_id, student_id=student_id
        )
        if tutorship is None:
            return await cls.create(tutor_id=tutor_id, student_id=student_id)
        return tutorship

    @classmethod
    async def find_paginated_by_tutor_id(
        cls,
        tutor_id: int,
        created_before: datetime | None,
        limit: int,
    ) -> Sequence[Self]:
        stmt = select(cls).filter_by(tutor_id=tutor_id)
        if created_before is not None:
            stmt = stmt.filter(cls.created_at < created_before)
        return await db.get_all(stmt.order_by(cls.created_at.desc()).limit(limit))

    @classmethod
    async def find_paginated_by_student_id(
        cls,
        student_id: int,
        created_before: datetime | None,
        limit: int,
    ) -> Sequence[Self]:
        stmt = select(cls).filter_by(student_id=student_id)
        if created_before is not None:
            stmt = stmt.filter(cls.created_at < created_before)
        return await db.get_all(stmt.order_by(cls.created_at.desc()).limit(limit))
