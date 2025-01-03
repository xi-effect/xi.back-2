from collections.abc import Sequence
from datetime import datetime
from typing import Annotated, Self
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import DateTime, ForeignKey, Index, Text, select
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
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    sender_user_id: Mapped[int] = mapped_column()
    chat_id: Mapped[int] = mapped_column(
        ForeignKey(Chat.id, ondelete="CASCADE"),
        index=True,
    )

    content: Mapped[str] = mapped_column(Text)
    pinned: Mapped[bool] = mapped_column(default=False)

    __table_args__ = (
        Index("created_at_sort_index", created_at.desc()),
        Index(
            "pinned_messages_created_at_sort_index",
            created_at.desc(),
            postgresql_where=(pinned.is_(True)),
        ),
    )

    ContentType = Annotated[str, Field(min_length=1, max_length=2000)]

    InputSchema = MappedModel.create(columns=[(content, ContentType)])
    PatchSchema = InputSchema.as_patch()
    InputMUBSchema = InputSchema.extend(columns=[sender_user_id, pinned])
    PatchMUBSchema = InputMUBSchema.as_patch()
    ResponseSchema = MappedModel.create(
        columns=[
            id,
            (content, ContentType),
            sender_user_id,
            pinned,
            created_at,
            updated_at,
        ]
    )
    ServerEventSchema = ResponseSchema.extend(columns=[chat_id])

    @classmethod
    async def find_by_chat_id_created_before(
        cls,
        chat_id: int,
        created_before: datetime | None,
        limit: int,
        only_pinned: bool = False,
    ) -> Sequence[Self]:
        stmt = select(cls).filter_by(chat_id=chat_id).order_by(cls.created_at.desc())

        if created_before is not None:
            stmt = stmt.filter(cls.created_at < created_before)

        if only_pinned:
            stmt = stmt.filter_by(pinned=True)

        return await db.get_all(stmt.limit(limit))


class MessageIdsSchema(BaseModel):
    chat_id: int
    message_id: UUID
