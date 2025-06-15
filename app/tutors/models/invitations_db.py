from datetime import datetime
from typing import Any, ClassVar, Self

from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import CHAR, DateTime, Index, select
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.functions import count

from app.common.config import Base
from app.common.cyptography import TokenGenerator
from app.common.sqlalchemy_ext import db
from app.common.utils.datetime import datetime_utc_now

invitation_token_generator = TokenGenerator(randomness=8, length=10)


class Invitation(Base):
    __tablename__ = "tutor_invitations"

    max_count: ClassVar[int] = 10

    id: Mapped[int] = mapped_column(primary_key=True)
    tutor_id: Mapped[int] = mapped_column()

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime_utc_now
    )
    code: Mapped[str] = mapped_column(
        CHAR(invitation_token_generator.token_length), unique=True
    )
    usage_count: Mapped[int] = mapped_column(default=0)

    __table_args__ = (
        Index("hash_index_tutor_invitations_code", code, postgresql_using="hash"),
    )

    ResponseSchema = MappedModel.create(columns=[id, created_at, code, usage_count])

    @classmethod
    async def create(cls, **kwargs: Any) -> Self:
        if kwargs.get("code") is None:
            code = invitation_token_generator.generate_token()
            kwargs["code"] = code
        return await super().create(**kwargs)

    @classmethod
    async def count_by_tutor_id(cls, tutor_id: int) -> int:
        stmt = select(count(cls.id)).filter(cls.tutor_id == tutor_id)
        return await db.get_count(stmt)
