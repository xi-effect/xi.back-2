from collections.abc import Sequence
from datetime import datetime, timezone
from typing import Any, ClassVar, Self

from pydantic import FutureDatetime, PositiveInt
from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import CHAR, DateTime, ForeignKey, Index, Row, or_, select
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.functions import count, func

from app.common.config import Base
from app.common.cyptography import TokenGenerator
from app.common.sqlalchemy_ext import db
from app.communities.models.communities_db import Community

invitation_token_generator = TokenGenerator(randomness=8, length=10)


class Invitation(Base):
    __tablename__ = "invitations"

    max_count: ClassVar[int] = 50

    # invitation data
    id: Mapped[int] = mapped_column(primary_key=True)
    token: Mapped[str] = mapped_column(CHAR(invitation_token_generator.token_length))
    # TODO rename back to code
    expiry: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # TODO naming for timestamps should be consistent with Participants
    usage_count: Mapped[int] = mapped_column(default=0)
    usage_limit: Mapped[int | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    # creator data
    creator_id: Mapped[int] = mapped_column()

    # community data
    community_id: Mapped[int] = mapped_column(
        ForeignKey(Community.id, ondelete="CASCADE")
    )
    community: Mapped[Community] = relationship(passive_deletes=True)

    # indexes
    __table_args__ = (
        Index(
            "hash_index_invitations_community_id", community_id, postgresql_using="hash"
        ),
        Index("hash_index_invitations_token", token, postgresql_using="hash"),
    )

    # schemas
    InputSchema = MappedModel.create(
        columns=[(expiry, FutureDatetime | None), (usage_limit, PositiveInt | None)],
    )
    MUBInputSchema = InputSchema.extend(columns=[created_at, creator_id])
    ResponseSchema = MappedModel.create(
        columns=[id, token, expiry, usage_count, usage_limit, created_at, creator_id]
    )

    @classmethod
    async def create(cls, **kwargs: Any) -> Self:
        if kwargs.get("token") is None:
            token = invitation_token_generator.generate_token()
            if (await Invitation.find_first_by_kwargs(token=token)) is not None:
                raise RuntimeError("Token collision happened (!wow!)")
            kwargs["token"] = token
        return await super().create(**kwargs)

    @classmethod
    def valid_only_filters(cls) -> Any:  # TODO SQLAlchemy uses private typing
        return (
            or_(cls.expiry.is_(None), cls.expiry >= func.now()),
            or_(
                cls.usage_limit.is_(None),
                cls.usage_count < cls.usage_limit,
            ),
        )

    @classmethod
    async def count_by_community_id(cls, community_id: int) -> int:
        return await db.get_count(
            select(count(cls.id)).filter(
                cls.community_id == community_id,
                *cls.valid_only_filters(),
            )
        )

    @classmethod
    async def find_all_valid_by_community_id(cls, community_id: int) -> Sequence[Self]:
        # TODO add sorting by creation time
        return await db.get_all(
            select(cls)
            .filter(
                cls.community_id == community_id,
                *cls.valid_only_filters(),
            )
            .order_by(cls.created_at)
        )

    @classmethod
    async def find_with_community_by_code(
        cls, code: str
    ) -> Row[tuple[Community, Self]] | None:
        return await db.get_first_row(
            select(Community, cls).join(cls).filter(cls.token == code).limit(1)
        )

    def is_valid(self) -> bool:
        return (
            self.expiry is None or self.expiry >= datetime.now(tz=timezone.utc)
        ) and (self.usage_limit is None or self.usage_limit > self.usage_count)
