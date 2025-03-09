from datetime import datetime
from typing import Any, ClassVar, Self

from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import CHAR, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base
from app.common.cyptography import TokenGenerator

invitation_token_generator = TokenGenerator(randomness=8, length=10)


class Invitation(Base):
    __tablename__ = "tutor_invitations"

    max_count: ClassVar[int] = 50

    # invitation data
    id: Mapped[int] = mapped_column(primary_key=True)
    tutor_id: Mapped[int] = mapped_column()
    code: Mapped[str] = mapped_column(
        CHAR(invitation_token_generator.token_length), unique=True
    )
    created_at: Mapped[datetime] = mapped_column(default=DateTime(timezone=True))
    usage_count: Mapped[int] = mapped_column(default=0)

    # indexes
    __table_args__ = (
        Index("hash_index_tutor_invitations_code", code, postgresql_using="hash"),
    )

    # schemas
    ResponseSchema = MappedModel.create(
        columns=[id, tutor_id, code, created_at, usage_count]
    )

    # class methods
    @classmethod
    async def create(cls, **kwargs: Any) -> Self:
        if kwargs.get("code") is None:
            code = invitation_token_generator.generate_token()
            if (await Invitation.find_first_by_kwargs(code=code)) is not None:
                raise RuntimeError("Code collision happend")
            kwargs["code"] = code
        return await super().create(**kwargs)
