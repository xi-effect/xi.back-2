from collections.abc import Sequence
from datetime import datetime
from typing import Self

from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import ForeignKey, Index, String, Text, select
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base
from app.common.sqlalchemy_ext import db
from app.communities.models.channels_db import Channel


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    author_id: Mapped[int] = mapped_column()
    channel_id: Mapped[int] = mapped_column(ForeignKey(Channel.id, ondelete="CASCADE"))

    __table_args__ = (
        Index("hash_index_posts_channel_id", channel_id, postgresql_using="hash"),
    )

    InputSchema = MappedModel.create(
        columns=[title, description, author_id],
    )
    PatchSchema = InputSchema.as_patch()
    ResponseSchema = InputSchema.extend(columns=[id, created_at])

    @classmethod
    async def find_paginated_by_channel_id(
        cls,
        channel_id: int,
        offset: int,
        limit: int,
    ) -> Sequence[Self]:
        stmt = (
            select(cls).filter_by(channel_id=channel_id).order_by(cls.created_at.desc())
        )
        return await db.get_paginated(stmt, offset, limit)
