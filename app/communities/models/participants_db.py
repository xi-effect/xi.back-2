from collections.abc import Sequence
from datetime import datetime

from pydantic import NaiveDatetime
from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import ForeignKey, Index, Select, select
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.config import Base
from app.common.sqlalchemy_ext import db
from app.communities.models.communities_db import Community


class Participant(Base):
    __tablename__ = "participants"

    # participant data
    id: Mapped[int] = mapped_column(primary_key=True)
    is_owner: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

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
    MUBBaseSchema = MappedModel.create(columns=[is_owner, (created_at, NaiveDatetime)])
    MUBPatchSchema = MUBBaseSchema.as_patch()
    FullResponseSchema = MUBBaseSchema.extend(columns=[id, user_id])

    # repository
    @classmethod
    def select_by_user_id(cls, user_id: int) -> Select[tuple[Community]]:
        return select(Community).join(cls).filter(cls.user_id == user_id)

    @classmethod
    async def find_first_community_by_user_id(cls, user_id: int) -> Community | None:
        return await db.get_first(cls.select_by_user_id(user_id).limit(1))

    @classmethod
    async def find_all_communities_by_user_id(cls, user_id: int) -> Sequence[Community]:
        return await db.get_all(cls.select_by_user_id(user_id))
