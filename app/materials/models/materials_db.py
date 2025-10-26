from collections.abc import Sequence
from datetime import datetime
from enum import StrEnum, auto
from typing import Annotated, Literal, Self

from pydantic import AwareDatetime, BaseModel, Field
from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import DateTime, Enum, Select, String, select
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base
from app.common.sqlalchemy_ext import db
from app.common.utils.datetime import datetime_utc_now


class MaterialAccessKind(StrEnum):
    TUTOR = auto()
    CLASSROOM = auto()


class MaterialContentKind(StrEnum):
    # TODO add files
    NOTE = auto()
    BOARD = auto()


class MaterialAccessMode(StrEnum):
    NO_ACCESS = auto()
    READ_ONLY = auto()
    READ_WRITE = auto()


class MaterialCursorSchema(BaseModel):
    created_at: AwareDatetime


class MaterialFiltersSchema(BaseModel):
    content_type: MaterialContentKind | None = None


class MaterialSearchRequestSchema(BaseModel):
    cursor: MaterialCursorSchema | None = None
    limit: Annotated[int, Field(gt=0, lt=100)] = 12
    filters: MaterialFiltersSchema


class Material(Base):
    __tablename__: str | None = "materials"

    id: Mapped[int] = mapped_column(primary_key=True)
    access_kind: Mapped[MaterialAccessKind] = mapped_column(Enum(MaterialAccessKind))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime_utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime_utc_now
    )

    name: Mapped[str] = mapped_column(String(length=100))

    access_group_id: Mapped[str] = mapped_column()
    content_kind: Mapped[MaterialContentKind] = mapped_column(Enum(MaterialContentKind))
    content_id: Mapped[str] = mapped_column()

    __mapper_args__ = {
        "polymorphic_on": access_kind,
        "polymorphic_abstract": True,
    }

    NameType = Annotated[str, Field(min_length=1, max_length=100)]

    NameSchema = MappedModel.create(columns=[(name, NameType)])
    BaseInputSchema = NameSchema.extend(columns=[content_kind])
    BasePatchSchema = NameSchema.as_patch()
    BaseResponseSchema = BaseInputSchema.extend(
        columns=[
            id,
            (created_at, AwareDatetime),
            (updated_at, AwareDatetime),
        ]
    )

    @classmethod
    def select_by_search_params(
        cls, search_params: MaterialSearchRequestSchema
    ) -> Select[tuple[Self]]:
        stmt = select(cls)

        if search_params.filters.content_type is not None:
            stmt = stmt.filter_by(content_kind=search_params.filters.content_type)

        if search_params.cursor is not None:
            stmt = stmt.filter(cls.created_at < search_params.cursor.created_at)

        return stmt.order_by(cls.created_at.desc()).limit(search_params.limit)


class TutorMaterial(Material):
    __tablename__ = None
    __mapper_args__ = {
        "polymorphic_identity": MaterialAccessKind.TUTOR,
        "polymorphic_load": "inline",
    }

    tutor_id: Mapped[int] = mapped_column(nullable=True)

    InputSchema = MappedModel.create(bases=[Material.BaseInputSchema])
    PatchSchema = MappedModel.create(bases=[Material.BasePatchSchema])
    ResponseSchema = MappedModel.create(
        bases=[Material.BaseResponseSchema],
        extra_fields={
            "kind": (Literal[MaterialAccessKind.TUTOR], MaterialAccessKind.TUTOR)
        },
    )

    @classmethod
    async def find_paginated_by_tutor(
        cls,
        tutor_id: int,
        search_params: MaterialSearchRequestSchema,
    ) -> Sequence[Self]:
        return await db.get_all(
            stmt=cls.select_by_search_params(search_params=search_params).filter_by(
                tutor_id=tutor_id
            )
        )


class ClassroomMaterial(Material):
    __tablename__ = None
    __mapper_args__ = {
        "polymorphic_identity": MaterialAccessKind.CLASSROOM,
        "polymorphic_load": "inline",
    }

    classroom_id: Mapped[int] = mapped_column(nullable=True)
    student_access_mode: Mapped[MaterialAccessMode] = mapped_column(nullable=True)

    StudentAccessModeSchema = MappedModel.create(columns=[student_access_mode])
    InputSchema = StudentAccessModeSchema.extend(bases=[Material.BaseInputSchema])
    PatchSchema = StudentAccessModeSchema.as_patch().extend(
        bases=[Material.BasePatchSchema]
    )
    ResponseSchema = StudentAccessModeSchema.extend(
        bases=[Material.BaseResponseSchema],
        extra_fields={
            "kind": (
                Literal[MaterialAccessKind.CLASSROOM],
                MaterialAccessKind.CLASSROOM,
            )
        },
    )

    @classmethod
    async def find_paginated_by_classroom(
        cls,
        classroom_id: int,
        only_accessible_to_students: bool,
        search_params: MaterialSearchRequestSchema,
    ) -> Sequence[Self]:
        stmt = cls.select_by_search_params(search_params=search_params)

        if only_accessible_to_students:
            stmt = stmt.filter(
                cls.student_access_mode.in_(
                    (MaterialAccessMode.READ_ONLY, MaterialAccessMode.READ_WRITE)
                )
            )

        return await db.get_all(stmt=stmt.filter_by(classroom_id=classroom_id))
