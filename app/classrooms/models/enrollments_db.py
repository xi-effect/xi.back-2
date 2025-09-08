from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, select
from sqlalchemy.orm import Mapped, mapped_column

from app.classrooms.models.classrooms_db import GroupClassroom
from app.common.config import Base
from app.common.sqlalchemy_ext import db
from app.common.utils.datetime import datetime_utc_now


class Enrollment(Base):
    __tablename__ = "enrollments"

    group_classroom_id: Mapped[int] = mapped_column(
        ForeignKey(GroupClassroom.id, ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    student_id: Mapped[int] = mapped_column(primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime_utc_now
    )

    @classmethod
    async def find_all_student_ids_by_classroom_id(
        cls, group_classroom_id: int
    ) -> Sequence[int]:
        return await db.get_all(
            select(cls.student_id)
            .filter_by(group_classroom_id=group_classroom_id)
            .order_by(cls.created_at.desc())
        )
