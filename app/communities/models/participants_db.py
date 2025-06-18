from collections.abc import Sequence
from datetime import datetime
from typing import Self

from pydantic import AwareDatetime
from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import DateTime, ForeignKey, Index, Row, select
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.config import Base
from app.common.sqlalchemy_ext import db
from app.common.utils.datetime import datetime_utc_now
from app.communities.models.communities_db import Community


class Participant(Base):
    __tablename__ = "participants"

    # participant data
    id: Mapped[int] = mapped_column(primary_key=True)
    is_owner: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime_utc_now
    )

    # user data
    user_id: Mapped[int] = mapped_column()

    # community data
    community_id: Mapped[int] = mapped_column(
        ForeignKey(Community.id, ondelete="CASCADE")
    )
    community: Mapped[Community] = relationship(passive_deletes=True)

    # indexes
    __table_args__ = (
        Index("hash_index_user_id", user_id, postgresql_using="hash"),
        Index("hash_index_community_id", community_id, postgresql_using="hash"),
    )

    # models
    CurrentSchema = MappedModel.create(columns=[is_owner])
    IDsSchema = MappedModel.create(columns=[community_id, user_id])
    MUBBaseSchema = CurrentSchema.extend(columns=[(created_at, AwareDatetime)])
    MUBPatchSchema = MUBBaseSchema.as_patch()
    MUBResponseSchema = MUBBaseSchema.extend(columns=[id, user_id])
    ListItemSchema = MUBBaseSchema.extend(columns=[user_id])
    ServerEventSchema = ListItemSchema.extend(columns=[community_id])

    # participant repository
    @classmethod
    async def find_all_by_community_id(cls, community_id: int) -> Sequence[Self]:
        # TODO pagination and search
        return await cls.find_all_by_kwargs(
            cls.created_at.desc(), community_id=community_id
        )

    # community-2-participant repository
    @classmethod
    async def find_first_community_by_user_id(
        cls, user_id: int
    ) -> Row[tuple[Community, Self]] | None:
        return await db.get_first_row(
            select(Community, cls).join(cls).filter(cls.user_id == user_id).limit(1)
        )

    @classmethod
    async def find_all_communities_by_user_id(cls, user_id: int) -> Sequence[Community]:
        return await db.get_all(
            select(Community).join(cls).filter(cls.user_id == user_id)
        )
