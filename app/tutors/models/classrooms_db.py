from datetime import datetime
from enum import StrEnum, auto
from typing import Annotated, Literal

from pydantic import AwareDatetime, Field
from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import DateTime, Enum, String, Text, select
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base
from app.common.sqlalchemy_ext import db
from app.common.utils.datetime import datetime_utc_now


class ClassroomKind(StrEnum):
    INDIVIDUAL = auto()
    GROUP = auto()


class ClassroomStatus(StrEnum):
    ACTIVE = auto()
    PAUSED = auto()
    LOCKED = auto()  # system-only
    FINISHED = auto()


UserClassroomStatus = Literal[
    ClassroomStatus.ACTIVE,
    ClassroomStatus.PAUSED,
    ClassroomStatus.FINISHED,
]


class Classroom(Base):
    __tablename__ = "classrooms"

    id: Mapped[int] = mapped_column(primary_key=True)
    tutor_id: Mapped[int] = mapped_column(index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime_utc_now
    )

    description: Mapped[str | None] = mapped_column(Text, default=None)
    kind: Mapped[ClassroomKind] = mapped_column(Enum(ClassroomKind))
    status: Mapped[ClassroomStatus] = mapped_column(
        Enum(ClassroomStatus), default=ClassroomStatus.ACTIVE
    )

    # TODO subject

    __mapper_args__ = {
        "polymorphic_on": kind,
        "polymorphic_abstract": True,
    }

    NameType = Annotated[str, Field(min_length=1, max_length=100)]
    DescriptionType = Annotated[str | None, Field(min_length=1)]

    BaseInputSchema = MappedModel.create(columns=[(description, DescriptionType)])
    TutorIDSchema = MappedModel.create(columns=[tutor_id])
    BaseResponseSchema = BaseInputSchema.extend(
        columns=[
            id,
            status,
            (created_at, AwareDatetime),
        ],
    )


class IndividualClassroom(Classroom):
    __tablename__ = None  # type: ignore[assignment]  # sqlalchemy magic
    __mapper_args__ = {
        "polymorphic_identity": ClassroomKind.INDIVIDUAL,
        "polymorphic_load": "inline",
    }

    tutor_name: Mapped[str] = mapped_column(String(100), nullable=True)

    student_id: Mapped[int] = mapped_column(nullable=True)
    student_name: Mapped[str] = mapped_column(String(100), nullable=True)

    InputSchema = MappedModel.create(bases=[Classroom.BaseInputSchema])
    PatchSchema = InputSchema.as_patch()
    BaseResponseSchema = MappedModel.create(
        bases=[Classroom.BaseResponseSchema],
        extra_fields={
            "kind": (Literal[ClassroomKind.INDIVIDUAL], ClassroomKind.INDIVIDUAL)
        },
    )
    TutorResponseSchema = BaseResponseSchema.extend(
        columns=[
            (student_id, int),
            (student_name, Classroom.NameType, "name"),
        ],
    )
    StudentResponseSchema = BaseResponseSchema.extend(
        bases=[Classroom.TutorIDSchema],
        columns=[(tutor_name, Classroom.NameType, "name")],
    )

    @classmethod
    async def find_classroom_id_by_users(
        cls, tutor_id: int, student_id: int
    ) -> int | None:
        return await db.get_first(
            select(cls.id).filter_by(
                tutor_id=tutor_id,
                student_id=student_id,
            )
        )


class GroupClassroom(Classroom):
    __tablename__ = None  # type: ignore[assignment]  # sqlalchemy magic
    __mapper_args__ = {
        "polymorphic_identity": ClassroomKind.GROUP,
        "polymorphic_load": "inline",
    }

    group_name: Mapped[str] = mapped_column(String(100), nullable=True)
    # TODO avatar?

    NameSchema = MappedModel.create(
        columns=[(group_name, Classroom.NameType, "name")],
    )
    InputSchema = NameSchema.extend(bases=[Classroom.BaseInputSchema])
    PatchSchema = InputSchema.as_patch()
    BaseResponseSchema = NameSchema.extend(
        bases=[Classroom.BaseResponseSchema],
        extra_fields={"kind": (Literal[ClassroomKind.GROUP], ClassroomKind.GROUP)},
    )
    TutorResponseSchema = BaseResponseSchema.extend()
    StudentPreviewSchema = NameSchema.extend()
    StudentResponseSchema = BaseResponseSchema.extend(
        bases=[Classroom.TutorIDSchema],
    )


AnyClassroom = IndividualClassroom | GroupClassroom

TutorClassroomResponseSchema = Annotated[  # schema for the tutor to see
    IndividualClassroom.TutorResponseSchema | GroupClassroom.TutorResponseSchema,
    Field(discriminator="kind"),
]
StudentClassroomResponseSchema = Annotated[  # schema for the student to see
    IndividualClassroom.StudentResponseSchema | GroupClassroom.StudentResponseSchema,
    Field(discriminator="kind"),
]
