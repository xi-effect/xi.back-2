from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base
from app.messenger.models.chats_db import Chat


class MessageDraft(Base):
    __tablename__ = "message_drafts"

    chat_id: Mapped[int] = mapped_column(
        ForeignKey(Chat.id, ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(primary_key=True)

    content: Mapped[str] = mapped_column(Text)

    InputSchema = MappedModel.create(columns=[content])
    PatchSchema = InputSchema.as_patch()
    ResponseSchema = InputSchema.extend([chat_id, user_id])
