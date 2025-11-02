from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.classrooms.models.classrooms_db import Classroom
from app.common.config import Base


class ClassroomNote(Base):
    __tablename__ = "classroom_notes"

    classroom_id: Mapped[int] = mapped_column(
        ForeignKey(Classroom.id, ondelete="CASCADE"),
        primary_key=True,
        autoincrement=False,
    )
    access_group_id: Mapped[str] = mapped_column()
    ydoc_id: Mapped[str] = mapped_column()
