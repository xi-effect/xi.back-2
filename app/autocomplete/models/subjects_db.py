from collections.abc import Sequence
from typing import Annotated, Self

from pydantic import Field
from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import Index, String, or_, select
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base
from app.common.sqlalchemy_ext import db


class Subject(Base):
    __tablename__ = "subjects"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    tutor_id: Mapped[int | None] = mapped_column(default=None)

    NameType = Annotated[str, Field(min_length=1, max_length=100)]

    InputSchema = MappedModel.create(columns=[(name, NameType)])
    InputMUBSchema = InputSchema.extend(columns=[tutor_id])
    PatchMUBSchema = InputMUBSchema.as_patch()
    ResponseMUBSchema = InputMUBSchema.extend(columns=[id])
    ResponseSchema = InputSchema.extend(columns=[id])

    __table_args__ = (
        Index("unique_index_subjects_tutor_id_name", "tutor_id", "name", unique=True),
    )

    @classmethod
    async def find_paginated_by_tutor_id(
        cls,
        tutor_id: int | None,
        offset: int,
        limit: int,
    ) -> Sequence[Self]:
        stmt = select(cls).order_by(cls.name)
        if tutor_id is None:
            stmt = stmt.filter(cls.tutor_id.is_(None))
        else:
            stmt = stmt.filter(or_(cls.tutor_id == tutor_id, cls.tutor_id.is_(None)))
        return await db.get_paginated(stmt, offset, limit)

    @classmethod
    async def is_present_by_name(cls, name: str, tutor_id: int | None) -> bool:
        stmt = select(cls).filter(
            cls.name == name,
            or_(cls.tutor_id == tutor_id, cls.tutor_id.is_(None)),
        )
        return await db.is_present(stmt)

    @classmethod
    async def find_for_autocomplete(cls, search: str, limit: int) -> Sequence[Self]:
        return await db.get_all(
            select(cls)
            .filter(cls.name.icontains(search.lower()))
            .order_by(cls.name)
            .limit(limit)
        )
