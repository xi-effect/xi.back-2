from datetime import datetime
from enum import StrEnum, auto
from typing import Self
from uuid import UUID, uuid4

from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import DateTime, Enum, LargeBinary, insert, literal, select
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base
from app.common.sqlalchemy_ext import db
from app.common.utils.datetime import datetime_utc_now


class YDocContentKind(StrEnum):
    NOTE = auto()
    BOARD = auto()


class YDoc(Base):
    __tablename__ = "ydocs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[int] = mapped_column(index=True)

    content_kind: Mapped[YDocContentKind] = mapped_column(
        Enum(YDocContentKind, name="content_ydoc_kind")
    )
    content: Mapped[bytes | None] = mapped_column(
        LargeBinary, default=None, deferred=True
    )
    size_bytes: Mapped[int] = mapped_column(default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime_utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime_utc_now
    )

    ResponseSchema = MappedModel.create(
        columns=[id, owner_id, content_kind, size_bytes, created_at, updated_at]
    )

    @classmethod
    async def duplicate_by_id(cls, source_ydoc_id: UUID, owner_id: int) -> Self:
        stmt = (
            insert(cls)
            .from_select(
                [cls.owner_id, cls.content_kind, cls.content, cls.size_bytes],
                (
                    select(
                        literal(owner_id),
                        cls.content_kind,
                        cls.content,
                        cls.size_bytes,
                    )
                    .select_from(cls)
                    .filter_by(id=source_ydoc_id)
                ),
            )
            .returning(cls)
        )
        return (await db.session.execute(stmt)).scalar_one()
