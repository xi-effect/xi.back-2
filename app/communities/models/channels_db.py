import enum
from collections.abc import Sequence
from typing import Self

from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.config import Base
from app.communities.models.categories_db import Category
from app.communities.models.communities_db import Community


class ChannelType(str, enum.Enum):
    POSTS = "posts"
    TASKS = "tasks"
    CHATS = "chats"
    VIDEO = "video"


class Channel(Base):
    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(primary_key=True)
    position: Mapped[int] = mapped_column()
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    kind: Mapped[ChannelType] = mapped_column(Enum(ChannelType))

    community_id: Mapped[int] = mapped_column(
        ForeignKey(Community.id, ondelete="CASCADE")
    )
    community: Mapped[Community] = relationship(passive_deletes=True)

    category_id: Mapped[int | None] = mapped_column(  # TODO remove cascade in future
        ForeignKey(Category.id, ondelete="CASCADE")
    )
    category: Mapped[Category | None] = relationship(passive_deletes=True)

    __table_args__ = (
        Index(
            "hash_index_channels_community_id", community_id, postgresql_using="hash"
        ),
        Index("hash_index_channels_category_id", community_id, postgresql_using="hash"),
    )

    BaseInputSchema = MappedModel.create(columns=[name, description])
    InputSchema = BaseInputSchema.extend(columns=[kind])
    PatchSchema = BaseInputSchema.as_patch()
    ResponseSchema = InputSchema.extend(columns=[id])

    @classmethod
    async def find_all_by_community_id(cls, community_id: int) -> Sequence[Self]:
        return await cls.find_all_by_kwargs(cls.position, community_id=community_id)
