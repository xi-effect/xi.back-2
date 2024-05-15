from collections.abc import Sequence
from typing import Self

from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.config import Base
from app.communities.models.communities_db import Community


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    position: Mapped[int] = mapped_column()
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)

    community_id: Mapped[int] = mapped_column(
        ForeignKey(Community.id, ondelete="CASCADE"), nullable=False
    )
    community: Mapped[Community] = relationship(passive_deletes=True)

    __table_args__ = (
        Index(
            "hash_index_categories_community_id", community_id, postgresql_using="hash"
        ),
    )

    InputSchema = MappedModel.create(columns=[name, description])
    PatchSchema = InputSchema.as_patch()
    ResponseSchema = InputSchema.extend(columns=[id])

    @classmethod
    async def find_all_by_community_id(cls, community_id: int) -> Sequence[Self]:
        return await cls.find_all_by_kwargs(cls.position, community_id=community_id)
