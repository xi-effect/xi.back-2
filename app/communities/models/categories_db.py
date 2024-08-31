from collections.abc import Sequence
from typing import Any, ClassVar, Self

from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.abscract_models.ordered_lists_db import (
    InvalidMoveException,
    SpacedOrderedList,
)
from app.communities.models.communities_db import Community


class Category(SpacedOrderedList[int]):
    __tablename__ = "categories"

    max_count_per_community: ClassVar[int] = 50

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
    ResponseSchema = InputSchema.extend(columns=[(SpacedOrderedList.id, int)])
    ServerEventSchema = ResponseSchema.extend(columns=[community_id])

    @property
    def list_id(self) -> int:  # noqa: FNE002  # list is not a verb
        return self.community_id

    @list_id.setter
    def list_id(self, list_id: int) -> None:
        self.community_id = list_id

    @classmethod
    def list_id_filter(cls, list_id: int) -> Any:
        return cls.community_id == list_id

    @classmethod
    async def find_all_by_community_id(cls, community_id: int) -> Sequence[Self]:
        return await cls.find_all_by_kwargs(cls.position, community_id=community_id)

    @classmethod
    async def is_limit_per_community_reached(cls, community_id: int) -> bool:
        return (
            await cls.count_by_kwargs(cls.id, community_id=community_id)
            >= cls.max_count_per_community
        )

    def validate_move_data(self, after_id: int | None, before_id: int | None) -> None:
        if after_id is None and before_id is None:  # TODO (33602197) pragma: no cover
            raise InvalidMoveException("after and before are both empty")
        super().validate_move_data(after_id=after_id, before_id=before_id)
