from datetime import datetime
from enum import StrEnum, auto
from uuid import UUID, uuid4

from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import DateTime, Enum, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base
from app.common.utils.datetime import datetime_utc_now


class YDocContentKind(StrEnum):
    NOTE = auto()
    BOARD = auto()


class YDoc(Base):
    __tablename__ = "ydocs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[int] = mapped_column()

    content_kind: Mapped[YDocContentKind] = mapped_column(
        Enum(YDocContentKind, name="content_ydoc_kind")
    )
    content: Mapped[bytes | None] = mapped_column(LargeBinary, default=None)
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

    def update_content(self, content: bytes | None) -> None:
        self.content = content
        self.size_bytes = 0 if content is None else len(content)
        self.updated_at = datetime_utc_now()
