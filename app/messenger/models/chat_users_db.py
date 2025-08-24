from datetime import datetime
from typing import Self

from pydantic import AwareDatetime
from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base
from app.messenger.models.chats_db import Chat


class ChatUser(Base):
    __tablename__ = "chat_users"

    chat_id: Mapped[int] = mapped_column(
        ForeignKey(Chat.id, ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(primary_key=True)

    last_message_read: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )

    InputSchema = MappedModel.create(
        columns=[(last_message_read, AwareDatetime | None)]
    )
    PatchSchema = InputSchema.as_patch()
    ResponseSchema = InputSchema.extend(columns=[chat_id, user_id])

    @classmethod
    async def find_or_create(cls, chat_id: int, user_id: int) -> Self:
        chat_user = await cls.find_first_by_kwargs(chat_id=chat_id, user_id=user_id)
        if chat_user is None:
            return await cls.create(chat_id=chat_id, user_id=user_id)
        return chat_user
