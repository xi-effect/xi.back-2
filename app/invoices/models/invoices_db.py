from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import Field
from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base
from app.common.utils.datetime import datetime_utc_now


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(primary_key=True)
    creator_user_id: Mapped[int] = mapped_column(index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime_utc_now
    )

    total: Mapped[Decimal] = mapped_column()
    comment: Mapped[str | None] = mapped_column(Text, default=None)

    CommentType = Annotated[str | None, Field(min_length=1, max_length=1000)]

    InputSchema = MappedModel.create(columns=[(comment, CommentType)])
    IDSchema = MappedModel.create(columns=[id])
