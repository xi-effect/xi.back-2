from collections.abc import Sequence
from typing import Annotated, ClassVar, Self

from pydantic import Field
from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import Enum, Index, String, or_, select
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base
from app.common.schemas.autocomplete_sch import TagKind
from app.common.sqlalchemy_ext import db


class Tag(Base):
    __tablename__: str | None = "tags"

    max_count_per_tutor_per_kind: ClassVar[int] = 100

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[TagKind] = mapped_column(Enum(TagKind))
    name: Mapped[str] = mapped_column(String(100))
    tutor_id: Mapped[int | None] = mapped_column(default=None)

    __mapper_args__ = {
        "polymorphic_on": kind,
        "polymorphic_abstract": True,
    }

    NameType = Annotated[str, Field(min_length=1, max_length=100)]

    InputSchema = MappedModel.create(columns=[(name, NameType)])
    PatchSchema = InputSchema.as_patch()
    InputMUBSchema = InputSchema.extend(columns=[tutor_id])
    PatchMUBSchema = InputMUBSchema.as_patch()
    ResponseMUBSchema = InputMUBSchema.extend(columns=[id])
    ResponseSchema = InputSchema.extend(columns=[id])

    __table_args__ = (
        Index(
            "unique_index_tags_kind_tutor_id_name",
            kind,
            tutor_id,
            name,
            unique=True,
        ),
    )

    @classmethod
    async def find_paginated_by_tutor_id(
        cls,
        tutor_id: int | None,
        offset: int,
        limit: int,
    ) -> Sequence[Self]:
        stmt = (
            select(cls)
            .filter(or_(cls.tutor_id == tutor_id, cls.tutor_id.is_(None)))
            .order_by(cls.name)
        )
        return await db.get_paginated(stmt, offset, limit)

    @classmethod
    async def is_present_by_name(cls, name: str, tutor_id: int | None) -> bool:
        stmt = select(cls).filter(
            cls.name == name,
            or_(cls.tutor_id == tutor_id, cls.tutor_id.is_(None)),
        )
        return await db.is_present(stmt)

    @classmethod
    async def is_limit_per_tutor_reached(cls, tutor_id: int) -> bool:
        return (
            await cls.count_by_kwargs(cls.id, tutor_id=tutor_id)
            >= cls.max_count_per_tutor_per_kind
        )

    @classmethod
    async def find_for_autocomplete(
        cls,
        search: str,
        tutor_id: int | None,
        limit: int,
    ) -> Sequence[Self]:
        return await db.get_all(
            select(cls)
            .filter(
                cls.name.icontains(search.lower()),
                or_(cls.tutor_id == tutor_id, cls.tutor_id.is_(None)),
            )
            .order_by(cls.name)
            .limit(limit)
        )

    @classmethod
    async def find_all_by_ids(
        cls,
        tag_ids: list[int],
        tutor_id: int | None = None,
    ) -> Sequence[Self]:
        stmt = select(cls).filter(cls.id.in_(tag_ids))
        if tutor_id is not None:
            stmt = stmt.filter(or_(cls.tutor_id == tutor_id, cls.tutor_id.is_(None)))
        return await db.get_all(stmt)


class SubjectTag(Tag):
    __tablename__ = None

    __mapper_args__ = {
        "polymorphic_identity": TagKind.SUBJECT,
        "polymorphic_load": "inline",
    }


class GenericTag(Tag):
    __tablename__ = None

    __mapper_args__ = {
        "polymorphic_identity": TagKind.GENERIC,
        "polymorphic_load": "inline",
    }


AnyTag = SubjectTag | GenericTag
