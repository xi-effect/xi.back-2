import enum
from collections.abc import Sequence
from typing import Any, ClassVar, Self

from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import Enum, ForeignKey, Index, String, Text, and_
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.abscract_models.ordered_lists_db import SpacedOrderedList
from app.communities.models.categories_db import Category
from app.communities.models.communities_db import Community


class ChannelType(str, enum.Enum):
    POSTS = "posts"
    TASKS = "tasks"
    CHATS = "chats"
    VIDEO = "video"
    BOARD = "board"


class Channel(SpacedOrderedList[tuple[int, int | None]]):
    __tablename__ = "channels"

    max_count_per_community: ClassVar[int] = 500
    max_count_per_category: ClassVar[int] = 50

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
        Index("hash_index_channels_category_id", category_id, postgresql_using="hash"),
    )

    BaseInputSchema = MappedModel.create(columns=[name, description])
    InputSchema = BaseInputSchema.extend(columns=[kind])
    PatchSchema = BaseInputSchema.as_patch()
    ResponseSchema = InputSchema.extend(columns=[(SpacedOrderedList.id, int)])

    @property
    def list_id(self) -> tuple[int, int | None]:  # noqa: FNE002  # list is not a verb
        return self.community_id, self.category_id

    @list_id.setter
    def list_id(self, list_id: tuple[int, int | None]) -> None:
        self.community_id, self.category_id = list_id

    @classmethod
    def list_id_filter(cls, list_id: tuple[int, int | None]) -> Any:
        community_id, category_id = list_id
        if category_id is None:
            return and_(cls.community_id == community_id, cls.category_id.is_(None))
        return cls.category_id == category_id

    @classmethod
    async def find_all_by_community_id(cls, community_id: int) -> Sequence[Self]:
        return await cls.find_all_by_kwargs(cls.position, community_id=community_id)

    @classmethod
    async def is_limit_per_community_reached(cls, community_id: int) -> bool:
        return (
            await cls.count_by_kwargs(cls.id, community_id=community_id)
            >= cls.max_count_per_community
        )

    @classmethod
    async def is_limit_per_category_reached(
        cls, community_id: int, category_id: int | None
    ) -> bool:
        return (
            await cls.count_by_kwargs(
                cls.id, community_id=community_id, category_id=category_id
            )
            >= cls.max_count_per_category
        )
