from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import Enum
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base
from app.common.schemas.messenger_sch import ChatAccessKind


class Chat(Base):
    __tablename__ = "chats"

    id: Mapped[int] = mapped_column(primary_key=True)

    access_kind: Mapped[ChatAccessKind] = mapped_column(Enum(ChatAccessKind))
    related_id: Mapped[str] = mapped_column()

    InputSchema = MappedModel.create(columns=[access_kind, related_id])
    ResponseSchema = InputSchema.extend(columns=[id])
