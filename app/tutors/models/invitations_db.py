from datetime import datetime
from typing import Any, Self

from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import CHAR, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base
from app.common.cyptography import TokenGenerator

invitation_token_generator = TokenGenerator(randomness=8, length=10)


class Invitation(Base):
    __tablename__ = "tutor_invitations"

    # tutor invitation data
    id: Mapped[int] = mapped_column(primary_key=True)
    tutor_id: Mapped[int] = mapped_column()
    code: Mapped[str] = mapped_column(
        CHAR(invitation_token_generator.token_length), unique=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now
    )
    usage_count: Mapped[int] = mapped_column(default=0)

    # indexes
    __table_args__ = (
        Index("hash_index_tutor_invitations_code", code, postgresql_using="hash"),
    )

    # schemas
    InputSchema = MappedModel.create(columns=[tutor_id])
    ResponseSchema = MappedModel.create(
        columns=[id, tutor_id, code, created_at, usage_count]
    )

    @classmethod
    async def create(cls, **kwargs: Any) -> Self:
        if kwargs.get("code") is None:
            code = invitation_token_generator.generate_token()
            kwargs["code"] = code
        return await super().create(**kwargs)
