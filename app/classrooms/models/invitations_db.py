from datetime import datetime
from typing import ClassVar, Self

from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import CHAR, DateTime, Enum, ForeignKey, select
from sqlalchemy.orm import Mapped, mapped_column, raiseload, relationship
from sqlalchemy.sql.functions import count

from app.classrooms.models.classrooms_db import ClassroomKind, GroupClassroom
from app.common.config import Base
from app.common.cyptography import TokenGenerator
from app.common.sqlalchemy_ext import db
from app.common.utils.datetime import datetime_utc_now

invitation_token_generator = TokenGenerator(randomness=8, length=10)


class Invitation(Base):
    __tablename__ = "tutor_invitations"

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[ClassroomKind] = mapped_column(Enum(ClassroomKind))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime_utc_now
    )
    code: Mapped[str] = mapped_column(
        CHAR(invitation_token_generator.token_length),
        default=invitation_token_generator.generate_token,
        index=True,
        unique=True,
    )
    usage_count: Mapped[int] = mapped_column(default=0)

    __mapper_args__ = {
        "polymorphic_on": kind,
        "polymorphic_abstract": True,
    }

    ResponseSchema = MappedModel.create(columns=[id, created_at, code, usage_count])


class IndividualInvitation(Invitation):
    __tablename__ = None  # type: ignore[assignment]  # sqlalchemy magic
    __mapper_args__ = {
        "polymorphic_identity": ClassroomKind.INDIVIDUAL,
        "polymorphic_load": "inline",
    }

    max_count_per_tutor: ClassVar[int] = 10

    tutor_id: Mapped[int] = mapped_column(index=True, nullable=True)

    @classmethod
    async def count_by_tutor_id(cls, tutor_id: int) -> int:
        stmt = select(count(cls.id)).filter(cls.tutor_id == tutor_id)
        return await db.get_count(stmt)


class GroupInvitation(Invitation):
    __tablename__ = None  # type: ignore[assignment]  # sqlalchemy magic
    __mapper_args__ = {
        "polymorphic_identity": ClassroomKind.GROUP,
        "polymorphic_load": "inline",
    }

    group_classroom_id: Mapped[int] = mapped_column(
        ForeignKey(GroupClassroom.id, ondelete="CASCADE"),
        index=True,
        unique=True,
        nullable=True,
    )
    group_classroom: Mapped[GroupClassroom] = relationship(lazy="joined")

    @property
    def tutor_id(self) -> int:
        return self.group_classroom.tutor_id

    @classmethod
    async def find_first_by_group_classroom_id(
        cls, group_classroom_id: int
    ) -> Self | None:
        return await db.get_first(
            select(cls)
            .options(raiseload(cls.group_classroom))
            .filter_by(group_classroom_id=group_classroom_id)
        )


AnyInvitation = IndividualInvitation | GroupInvitation
