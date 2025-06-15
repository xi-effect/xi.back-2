from collections.abc import Sequence
from datetime import datetime
from enum import StrEnum
from typing import Annotated, Self

from pydantic import Field
from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import DateTime, Enum, String, select
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base
from app.common.sqlalchemy_ext import db
from app.common.utils.datetime import datetime_utc_now


class MaterialKind(StrEnum):
    NOTE = "note"
    BOARD = "board"


class Material(Base):
    __tablename__ = "tutor_materials"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(length=100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime_utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime_utc_now
    )
    last_opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime_utc_now
    )
    tutor_id: Mapped[int] = mapped_column()
    kind: Mapped[MaterialKind] = mapped_column(Enum(MaterialKind))

    NameType = Annotated[str, Field(min_length=1, max_length=100)]

    BaseInputSchema = MappedModel.create(columns=[(name, NameType)])
    InputSchema = BaseInputSchema.extend([kind])
    PatchSchema = BaseInputSchema.as_patch()
    ResponseSchema = MappedModel.create(
        columns=[id, name, created_at, updated_at, last_opened_at, kind]
    )

    @classmethod
    async def find_paginated_by_tutor(
        cls,
        tutor_id: int,
        last_opened_before: datetime | None,
        kind: MaterialKind | None,
        limit: int,
    ) -> Sequence[Self]:
        stmt = select(cls).filter_by(tutor_id=tutor_id)

        if kind is not None:
            stmt = stmt.filter_by(kind=kind)

        if last_opened_before is not None:
            stmt = stmt.filter(cls.last_opened_at < last_opened_before)

        return await db.get_all(
            stmt=stmt.order_by(cls.last_opened_at.desc()).limit(limit)
        )
