from collections.abc import Sequence
from datetime import datetime
from typing import Annotated, Self
from uuid import UUID, uuid4

from pydantic import Field
from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import DateTime, ForeignKey, Text, select
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base
from app.common.sqlalchemy_ext import db
from app.common.utils.datetime import datetime_utc_now
from app.messenger.models.chats_db import Chat


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime_utc_now,
        index=True,
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    sender_user_id: Mapped[int] = mapped_column()
    chat_id: Mapped[int] = mapped_column(
        ForeignKey(Chat.id, ondelete="CASCADE"),
        index=True,
    )

    content: Mapped[str] = mapped_column(Text)

    ContentType = Annotated[str, Field(min_length=1, max_length=2000)]

    InputSchema = MappedModel.create(columns=[(content, ContentType)])
    PatchSchema = InputSchema.as_patch()
    InputMUBSchema = InputSchema.extend(columns=[sender_user_id])
    ResponseSchema = MappedModel.create(
        columns=[id, (content, ContentType), sender_user_id, created_at, updated_at]
    )

    @classmethod
    async def find_paginated_by_chat_id(
        cls,
        chat_id: int,
        offset: int,
        limit: int,
    ) -> Sequence[Self]:
        stmt = select(cls).filter_by(chat_id=chat_id).order_by(cls.created_at.desc())
        return await db.get_paginated(stmt, offset, limit)
