from collections.abc import Sequence
from datetime import datetime
from enum import StrEnum, auto
from typing import Annotated, Literal, Self
from uuid import UUID, uuid4

from pydantic import AwareDatetime, BaseModel, Field
from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    and_,
    select,
    update,
)
from sqlalchemy.orm import Mapped, contains_eager, mapped_column, relationship

from app.common.config import Base
from app.common.sqlalchemy_ext import db
from app.common.utils.datetime import datetime_utc_now
from app.content.models.ydocs_db import YDoc, YDocContentKind


class MaterialAccessKind(StrEnum):
    PERSONAL = auto()
    CLASSROOM = auto()


class MaterialAccessMode(StrEnum):
    NO_ACCESS = auto()
    READ_ONLY = auto()
    READ_WRITE = auto()


STUDENT_ACCESSIBLE_ACCESS_MODES = (
    MaterialAccessMode.READ_ONLY,
    MaterialAccessMode.READ_WRITE,
)


class MaterialCursorSchema(BaseModel):
    updated_at: AwareDatetime


class MaterialFiltersSchema(BaseModel):
    content_kind: YDocContentKind | None = None


class MaterialSearchRequestSchema(BaseModel):
    cursor: MaterialCursorSchema | None = None
    limit: Annotated[int, Field(gt=0, lt=100)] = 12
    filters: MaterialFiltersSchema


class Material(Base):
    __tablename__: str | None = "materials"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    access_kind: Mapped[MaterialAccessKind] = mapped_column(
        Enum(MaterialAccessKind, name="content_material_access_kind")
    )

    main_ydoc_id: Mapped[UUID] = mapped_column(ForeignKey(YDoc.id), unique=True)
    main_ydoc: Mapped[YDoc] = relationship(lazy="joined")

    name: Mapped[str] = mapped_column(String(100))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime_utc_now
    )

    @property
    def content_kind(self) -> YDocContentKind:
        return self.main_ydoc.content_kind

    __mapper_args__ = {
        "polymorphic_on": access_kind,
        "polymorphic_abstract": True,
    }

    NameType = Annotated[str, Field(min_length=1, max_length=100)]

    NameSchema = MappedModel.create(columns=[(name, NameType)])
    BaseInputSchema = NameSchema.extend(properties=[content_kind])
    BasePatchSchema = NameSchema.as_patch()
    BaseResponseSchema = BaseInputSchema.extend(
        columns=[id, (updated_at, AwareDatetime)]
    )

    @classmethod
    async def update_main_ydoc_content(
        cls,
        main_ydoc_id: UUID,
        content: bytes | None,
    ) -> None:
        current_timestamp = datetime_utc_now()
        updated_ydocs = (
            update(YDoc)
            .filter_by(id=main_ydoc_id)
            .values(
                content=content,
                size_bytes=0 if content is None else len(content),
                updated_at=current_timestamp,
            )
            .returning(YDoc.id)
            .cte()
        )
        stmt = (
            update(cls)
            .filter(cls.main_ydoc_id.in_(select(updated_ydocs.c.id)))
            .values(updated_at=current_timestamp)
        )
        await db.session.execute(stmt)


class PersonalMaterial(Material):
    __tablename__ = None
    __mapper_args__ = {
        "polymorphic_identity": MaterialAccessKind.PERSONAL,
        "polymorphic_load": "inline",
    }

    tutor_id: Mapped[int] = mapped_column(nullable=True)

    InputSchema = MappedModel.create(bases=[Material.BaseInputSchema])
    PatchSchema = MappedModel.create(bases=[Material.BasePatchSchema])
    ResponseSchema = MappedModel.create(
        bases=[Material.BaseResponseSchema],
        extra_fields={
            "access_kind": (
                Literal[MaterialAccessKind.PERSONAL],
                MaterialAccessKind.PERSONAL,
            ),
        },
    )


class ClassroomMaterial(Material):
    __tablename__ = None
    __mapper_args__ = {
        "polymorphic_identity": MaterialAccessKind.CLASSROOM,
        "polymorphic_load": "inline",
    }

    classroom_id: Mapped[int] = mapped_column(nullable=True)
    student_access_mode: Mapped[MaterialAccessMode] = mapped_column(
        Enum(MaterialAccessMode, name="content_material_access_mode"),
        nullable=True,
    )

    StudentAccessModeSchema = MappedModel.create(
        columns=[(student_access_mode, MaterialAccessMode)]
    )
    DuplicateInputSchema = StudentAccessModeSchema.extend(bases=[Material.NameSchema])
    InputSchema = StudentAccessModeSchema.extend(bases=[Material.BaseInputSchema])
    PatchSchema = StudentAccessModeSchema.as_patch().extend(
        bases=[Material.BasePatchSchema]
    )
    ResponseSchema = StudentAccessModeSchema.extend(
        bases=[Material.BaseResponseSchema],
        extra_fields={
            "access_kind": (
                Literal[MaterialAccessKind.CLASSROOM],
                MaterialAccessKind.CLASSROOM,
            ),
        },
    )

    @classmethod
    async def find_paginated_by_classroom_id(
        cls,
        classroom_id: int,
        only_accessible_to_students: bool,
        search_params: MaterialSearchRequestSchema,
    ) -> Sequence[Self]:
        stmt = (
            select(cls)
            .filter_by(classroom_id=classroom_id)
            .join(cls.main_ydoc)
            .options(contains_eager(cls.main_ydoc))
        )

        if search_params.filters.content_kind is not None:
            stmt = stmt.filter(YDoc.content_kind == search_params.filters.content_kind)

        if only_accessible_to_students:
            stmt = stmt.filter(
                cls.student_access_mode.in_(STUDENT_ACCESSIBLE_ACCESS_MODES)
            )

        if search_params.cursor is not None:
            stmt = stmt.filter(cls.updated_at < search_params.cursor.updated_at)

        return await db.get_all(
            stmt.order_by(cls.updated_at.desc()).limit(search_params.limit)
        )


# declared outside the class, because STI doesn't support indexes on child classes
Index(
    "index_materials_classroom_id_updated_at",
    ClassroomMaterial.classroom_id,
    ClassroomMaterial.updated_at,
    postgresql_where=Material.access_kind == MaterialAccessKind.CLASSROOM,
)
Index(
    "index_materials_student_accessible_classroom_id_updated_at",
    ClassroomMaterial.classroom_id,
    ClassroomMaterial.updated_at,
    postgresql_where=and_(
        Material.access_kind == MaterialAccessKind.CLASSROOM,
        ClassroomMaterial.student_access_mode.in_(STUDENT_ACCESSIBLE_ACCESS_MODES),
    ),
)
