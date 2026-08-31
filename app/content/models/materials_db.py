from collections.abc import Iterable, Sequence
from datetime import datetime
from enum import StrEnum, auto
from typing import Annotated, ClassVar, Literal, Self, assert_never
from uuid import UUID, uuid4

from pydantic import AwareDatetime, BaseModel, Field
from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Select,
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
    CLASSROOM_NOTE = auto()


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


class BaseMaterialFiltersSchema(BaseModel):
    content_kind: YDocContentKind | None = None
    tag_ids: Annotated[set[int] | None, Field(min_length=1, max_length=5)] = None


class PersonalMaterialScopeSchema(BaseModel):
    access_kind: Literal[MaterialAccessKind.PERSONAL] = MaterialAccessKind.PERSONAL


class ClassroomMaterialScopeSchema(BaseModel):
    access_kind: Literal[MaterialAccessKind.CLASSROOM] = MaterialAccessKind.CLASSROOM
    classroom_ids: Annotated[list[int] | None, Field(min_length=1, max_length=20)] = (
        None
    )


AnyMaterialScopeSchema = Annotated[
    PersonalMaterialScopeSchema | ClassroomMaterialScopeSchema,
    Field(discriminator="access_kind"),
]


class AnyMaterialFiltersSchema(BaseMaterialFiltersSchema):
    scope: AnyMaterialScopeSchema | None = None


class BaseMaterialSearchRequestSchema(BaseModel):
    cursor: MaterialCursorSchema | None = None
    limit: Annotated[int, Field(gt=0, lt=100)] = 12


class AnyMaterialSearchRequestSchema(BaseMaterialSearchRequestSchema):
    filters: AnyMaterialFiltersSchema


class ClassroomMaterialFiltersSchema(BaseMaterialFiltersSchema):
    pass


class ClassroomMaterialSearchRequestSchema(BaseMaterialSearchRequestSchema):
    filters: ClassroomMaterialFiltersSchema

    def to_any_material_search_params(
        self,
        classroom_id: int,
    ) -> AnyMaterialSearchRequestSchema:
        return AnyMaterialSearchRequestSchema(
            cursor=self.cursor,
            limit=self.limit,
            filters=AnyMaterialFiltersSchema(
                content_kind=self.filters.content_kind,
                tag_ids=self.filters.tag_ids,
                scope=ClassroomMaterialScopeSchema(classroom_ids=[classroom_id]),
            ),
        )


class Material(Base):
    __tablename__: str | None = "materials"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    access_kind: Mapped[MaterialAccessKind] = mapped_column(
        Enum(MaterialAccessKind, name="content_material_access_kind")
    )

    main_ydoc_id: Mapped[UUID] = mapped_column(ForeignKey(YDoc.id), unique=True)
    main_ydoc: Mapped[YDoc] = relationship(lazy="joined")

    material_tags: Mapped[list["MaterialTag"]] = relationship(
        lazy="selectin", passive_deletes="all"
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime_utc_now
    )

    @property
    def content_kind(self) -> YDocContentKind:
        return self.main_ydoc.content_kind

    @property
    def tag_ids(self) -> list[int]:
        return [material_tag.tag_id for material_tag in self.material_tags]

    __mapper_args__ = {
        "polymorphic_on": access_kind,
        "polymorphic_abstract": True,
        # `polymorphic_load: inline` doesn't work in complex queries for some reason
        "with_polymorphic": "*",
    }

    ContentKindSchema = MappedModel.create(properties=[content_kind])
    BaseResponseSchema = ContentKindSchema.extend(
        columns=[id, (updated_at, AwareDatetime)],
        properties=[tag_ids],
    )

    @classmethod
    def select_by_search_params(
        cls,
        search_params: AnyMaterialSearchRequestSchema,
    ) -> Select[tuple[Self]]:
        stmt = select(cls)

        scope = search_params.filters.scope
        if scope is not None:
            stmt = stmt.filter_by(access_kind=scope.access_kind)
            match scope:
                case PersonalMaterialScopeSchema():
                    pass
                case ClassroomMaterialScopeSchema():
                    if scope.classroom_ids is not None:
                        stmt = stmt.filter(
                            ClassroomMaterial.classroom_id.in_(scope.classroom_ids)
                        )
                case _:
                    assert_never(scope)

        stmt = stmt.join(cls.main_ydoc).options(contains_eager(cls.main_ydoc))

        if search_params.filters.content_kind is not None:
            stmt = stmt.filter(YDoc.content_kind == search_params.filters.content_kind)

        if search_params.filters.tag_ids is not None:
            for tag_id in search_params.filters.tag_ids:
                stmt = stmt.filter(
                    select(MaterialTag)
                    .filter(
                        MaterialTag.material_id == cls.id,
                        MaterialTag.tag_id == tag_id,
                    )
                    .exists()
                )

        if search_params.cursor is not None:
            stmt = stmt.filter(cls.updated_at < search_params.cursor.updated_at)

        return stmt.order_by(cls.updated_at.desc()).limit(search_params.limit)

    @classmethod
    async def find_paginated_by_owner_id(
        cls,
        owner_id: int,
        default_allowed_access_kinds: Iterable[MaterialAccessKind],
        search_params: AnyMaterialSearchRequestSchema,
    ) -> Sequence[Self]:
        stmt = cls.select_by_search_params(search_params=search_params).filter(
            YDoc.owner_id == owner_id
        )

        if search_params.filters.scope is None:
            stmt = stmt.filter(cls.access_kind.in_(default_allowed_access_kinds))

        return await db.get_all(stmt)

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


class NamedMaterial(Material):
    __tablename__ = None
    __mapper_args__ = {
        "polymorphic_abstract": True,
    }

    name: Mapped[str] = mapped_column(String(100), nullable=True)

    NameType = Annotated[str, Field(min_length=1, max_length=100)]

    NameSchema = MappedModel.create(columns=[(name, NameType)])
    BaseInputSchema = NameSchema.extend(bases=[Material.ContentKindSchema])
    BasePatchSchema = NameSchema.as_patch()
    BaseResponseSchema = NameSchema.extend(bases=[Material.BaseResponseSchema])


class PersonalMaterial(NamedMaterial):
    __tablename__ = None
    __mapper_args__ = {
        "polymorphic_identity": MaterialAccessKind.PERSONAL,
        "polymorphic_load": "inline",
    }

    tutor_id: Mapped[int] = mapped_column(nullable=True)

    InputSchema = MappedModel.create(bases=[NamedMaterial.BaseInputSchema])
    PatchSchema = MappedModel.create(bases=[NamedMaterial.BasePatchSchema])
    ResponseSchema = MappedModel.create(
        bases=[NamedMaterial.BaseResponseSchema],
        extra_fields={
            "access_kind": (
                Literal[MaterialAccessKind.PERSONAL],
                MaterialAccessKind.PERSONAL,
            ),
        },
    )


class ClassroomMaterial(NamedMaterial):
    __tablename__ = None
    __mapper_args__ = {
        "polymorphic_identity": MaterialAccessKind.CLASSROOM,
        "polymorphic_load": "inline",
    }

    classroom_id: Mapped[int] = mapped_column(nullable=True, use_existing_column=True)
    student_access_mode: Mapped[MaterialAccessMode] = mapped_column(
        Enum(MaterialAccessMode, name="content_material_access_mode"),
        nullable=True,
    )

    StudentAccessModeSchema = MappedModel.create(
        columns=[(student_access_mode, MaterialAccessMode)]
    )
    DuplicateInputSchema = StudentAccessModeSchema.extend(
        bases=[NamedMaterial.NameSchema]
    )
    InputSchema = StudentAccessModeSchema.extend(bases=[NamedMaterial.BaseInputSchema])
    PatchSchema = StudentAccessModeSchema.as_patch().extend(
        bases=[NamedMaterial.BasePatchSchema]
    )
    ResponseSchema = StudentAccessModeSchema.extend(
        bases=[NamedMaterial.BaseResponseSchema],
        columns=[classroom_id],
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
        search_params: ClassroomMaterialSearchRequestSchema,
    ) -> Sequence[Self]:
        stmt = cls.select_by_search_params(
            search_params=search_params.to_any_material_search_params(
                classroom_id=classroom_id,
            ),
        )

        if only_accessible_to_students:
            stmt = stmt.filter(
                cls.student_access_mode.in_(STUDENT_ACCESSIBLE_ACCESS_MODES)
            )

        return await db.get_all(stmt)


class ClassroomNoteMaterial(Material):
    __tablename__ = None
    __mapper_args__ = {
        "polymorphic_identity": MaterialAccessKind.CLASSROOM_NOTE,
        "polymorphic_load": "inline",
    }

    classroom_id: Mapped[int] = mapped_column(nullable=True, use_existing_column=True)

    @classmethod
    async def is_present_by_classroom_id(cls, classroom_id: int) -> bool:
        return await db.is_present(select(cls).filter_by(classroom_id=classroom_id))


# declared outside the class, because STI doesn't support indexes on child classes
Index(
    "index_classroom_materials_pagination",
    ClassroomMaterial.classroom_id,
    ClassroomMaterial.updated_at,
    postgresql_where=Material.access_kind == MaterialAccessKind.CLASSROOM,
)
Index(
    "index_student_accessible_classroom_materials_pagination",
    ClassroomMaterial.classroom_id,
    ClassroomMaterial.updated_at,
    postgresql_where=and_(
        Material.access_kind == MaterialAccessKind.CLASSROOM,
        ClassroomMaterial.student_access_mode.in_(STUDENT_ACCESSIBLE_ACCESS_MODES),
    ),
)
Index(
    "unique_index_classroom_note_materials_classroom_id",
    ClassroomNoteMaterial.classroom_id,
    unique=True,
    postgresql_where=Material.access_kind == MaterialAccessKind.CLASSROOM_NOTE,
)


class MaterialTag(Base):
    __tablename__ = "material_tags"

    max_count_per_material: ClassVar[int] = 5

    material_id: Mapped[UUID] = mapped_column(
        ForeignKey(Material.id, ondelete="CASCADE"),
        primary_key=True,
    )
    tag_id: Mapped[int] = mapped_column(primary_key=True)

    @classmethod
    async def replace_all_by_material_id(
        cls,
        material_id: UUID,
        tag_ids: set[int],
    ) -> None:
        await cls.delete_by_kwargs(material_id=material_id)
        if len(tag_ids) != 0:
            await cls.create_batch(
                {"material_id": material_id, "tag_id": tag_id} for tag_id in tag_ids
            )


AnyNamedMaterial = PersonalMaterial | ClassroomMaterial

NAMED_MATERIAL_ACCESS_KINDS = (
    MaterialAccessKind.PERSONAL,
    MaterialAccessKind.CLASSROOM,
)

AnyNamedMaterialResponseSchema = Annotated[
    PersonalMaterial.ResponseSchema | ClassroomMaterial.ResponseSchema,
    Field(discriminator="access_kind"),
]
