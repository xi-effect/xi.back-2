from datetime import datetime
from typing import Any, ClassVar, Self

from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import CHAR, DateTime, ForeignKey, Index, or_, select
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.functions import count, func

from app.common.config import Base, token_generator
from app.common.sqlalchemy_ext import db
from app.communities.models.communities_db import Community


class Invitation(Base):
    __tablename__ = "invitations"

    max_count: ClassVar[int] = 50

    id: Mapped[int] = mapped_column(primary_key=True)
    token: Mapped[str] = mapped_column(CHAR(token_generator.token_length))
    expiry: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    usage_count: Mapped[int] = mapped_column(default=0)
    usage_limit: Mapped[int | None] = mapped_column()

    community_id: Mapped[int] = mapped_column(
        ForeignKey(Community.id, ondelete="CASCADE"), nullable=False
    )
    community: Mapped[Community] = relationship(passive_deletes=True)

    __table_args__ = (
        Index(
            "hash_index_invitations_community_id", community_id, postgresql_using="hash"
        ),
    )

    FullInputSchema = MappedModel.create(columns=[expiry, usage_limit])
    FullResponseSchema = FullInputSchema.extend(columns=[id, token, usage_count])

    @classmethod
    async def create(cls, **kwargs: Any) -> Self:
        if kwargs.get("token") is None:
            token = token_generator.generate_token()
            if (await Invitation.find_first_by_kwargs(token=token)) is not None:
                raise RuntimeError("Token collision happened (!wow!)")
            kwargs["token"] = token
        return await super().create(**kwargs)

    @classmethod
    async def count_by_community_id(cls, community_id: int) -> int:
        return await db.get_first(
            select(count(cls.id)).filter(
                cls.community_id == community_id,
                or_(cls.expiry.is_(None), cls.expiry >= func.now()),
                or_(
                    cls.usage_limit.is_(None),
                    cls.usage_count < cls.usage_limit,
                ),
            )
        )  # type: ignore[return-value]
