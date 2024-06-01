from typing import Any, ClassVar, Generic, Self, TypeVar

from sqlalchemy import func, select, update
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base
from app.common.sqlalchemy_ext import db

ListID = TypeVar("ListID")


class InvalidMoveException(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message

    def __str__(self) -> str:
        return f"Invalid move: {self.message}"


class SpacedOrderedList(Base, Generic[ListID]):
    __abstract__ = True

    spacing: ClassVar[int] = 1 << 12
    min_position: ClassVar[int] = -(spacing * 500)
    max_position: ClassVar[int] = spacing * 1000

    # column name specified twice for pydantic-marshals
    id: Mapped[int] = mapped_column("id", primary_key=True)
    position: Mapped[int] = mapped_column()

    @property
    def list_id(self) -> ListID:  # noqa: FNE002  # list is not a verb
        raise NotImplementedError

    @list_id.setter
    def list_id(self, list_id: ListID) -> None:
        raise NotImplementedError

    @classmethod
    def list_id_filter(cls, list_id: ListID) -> Any:
        raise NotImplementedError

    @classmethod
    async def reindex_by_list_id(cls, list_id: ListID) -> None:
        subquery = (
            select(
                cls.id,
                func.row_number().over(order_by=cls.position).label("row_number"),
            )
            .filter(cls.list_id_filter(list_id))
            .cte("ranked")
        )

        await db.session.execute(
            update(cls)
            .values(position=(subquery.c.row_number - 1) * cls.spacing)
            .where(cls.id == subquery.c.id, cls.list_id_filter(list_id))
        )

    @classmethod
    async def find_start_by_list_id(cls, list_id: ListID) -> Self | None:
        return await db.get_first(
            select(cls).filter(cls.list_id_filter(list_id)).order_by(cls.position)
        )

    @classmethod
    async def find_end_by_list_id(cls, list_id: ListID) -> Self | None:
        return await db.get_first(
            select(cls)
            .filter(cls.list_id_filter(list_id))
            .order_by(cls.position.desc())
        )

    @classmethod
    async def is_list_empty(cls, list_id: ListID) -> bool:
        return await db.is_absent(select(cls.id).filter(cls.list_id_filter(list_id)))

    @classmethod
    async def is_there_no_entries_in_between(cls, left: Self, right: Self) -> bool:
        return await db.is_absent(
            select(cls.id).filter(
                cls.list_id_filter(left.list_id),
                cls.position > left.position,
                cls.position < right.position,
            )
        )

    @classmethod
    async def are_entries_sequential(cls, left: Self, right: Self) -> bool:
        return (
            left.list_id == right.list_id
            and left.position >= right.position
            and (await cls.is_there_no_entries_in_between(left, right))
        )

    async def is_after(self, other: Self) -> bool:
        return await self.are_entries_sequential(other, self)

    async def is_before(self, other: Self) -> bool:
        return await self.are_entries_sequential(self, other)

    async def is_first(self) -> bool:
        return await db.is_absent(
            select(type(self).id).filter(
                self.list_id_filter(self.list_id),
                type(self).position < self.position,
            )
        )

    async def is_last(self) -> bool:
        return await db.is_absent(
            select(type(self).id).filter(
                self.list_id_filter(self.list_id),
                type(self).position > self.position,
            )
        )

    async def move_to_empty_list(self, list_id: ListID) -> None:
        # list should be confirmed empty via `cls.is_list_empty`
        self.list_id = list_id
        self.position = 0

    async def move_before_first(self, first: Self) -> None:
        self.list_id = first.list_id
        self.position = first.position - self.spacing
        if self.position < self.min_position:
            await self.reindex_by_list_id(list_id=self.list_id)

    async def move_to_start(self, list_id: ListID) -> None:
        first = await self.find_start_by_list_id(list_id=list_id)
        if first is None:
            await self.move_to_empty_list(list_id)
        else:
            await self.move_before_first(first)

    async def move_to_middle(self, after: Self, before: Self) -> None:
        self.list_id = after.list_id
        self.position = (after.position + before.position) // 2
        if self.position - after.position == 1 or before.position - self.position == 1:
            await self.reindex_by_list_id(list_id=self.list_id)

    async def move_after_last(self, last: Self) -> None:
        self.list_id = last.list_id
        self.position = last.position + self.spacing
        if self.position > self.max_position:
            await self.reindex_by_list_id(list_id=self.list_id)

    async def move_to_end(self, list_id: ListID) -> None:
        last = await self.find_end_by_list_id(list_id=list_id)
        if last is None:
            await self.move_to_empty_list(list_id)
        else:
            await self.move_after_last(last)

    @classmethod
    async def create(cls, **kwargs: Any) -> Self:
        entry = cls(**kwargs)  # noqa
        if "position" not in kwargs:
            await entry.move_to_end(list_id=entry.list_id)
        db.session.add(entry)
        await db.session.flush()
        return entry

    def validate_move_data(self, after_id: int | None, before_id: int | None) -> None:
        if after_id is not None and after_id == before_id:
            raise InvalidMoveException("after and before are the same")
        if after_id == self.id:
            raise InvalidMoveException("after and target are the same")
        if before_id == self.id:
            raise InvalidMoveException("target and before are the same")

    @classmethod
    async def find_first_by_id_or_none(
        cls, entry_id: int | None, list_id: ListID, name: str
    ) -> Self | None:
        if entry_id is None:
            return None

        entry = await cls.find_first_by_id(entry_id)
        if entry is None:
            raise InvalidMoveException(f"{name} not found")
        if entry.list_id != list_id:
            raise InvalidMoveException(f"{name} is in a different sub-list")
        return entry

    async def validate_and_move(
        self,
        list_id: ListID,
        after_id: int | None,
        before_id: int | None,
    ) -> None:
        self.validate_move_data(after_id=after_id, before_id=before_id)

        after = await self.find_first_by_id_or_none(after_id, list_id, name="after")
        before = await self.find_first_by_id_or_none(before_id, list_id, name="before")

        if after is not None and before is not None:
            if after.position >= before.position:
                raise InvalidMoveException("after and before are in the wrong order")

            if not await self.is_there_no_entries_in_between(after, before):
                raise InvalidMoveException("there are entries between after and before")

            await self.move_to_middle(after, before)
        elif before is not None:
            if not await before.is_first():
                raise InvalidMoveException("after is empty, but before is not first")

            await self.move_before_first(before)
        elif after is not None:
            if not await after.is_last():
                raise InvalidMoveException("before is empty, but after is not last")

            await self.move_after_last(after)
        else:
            if not await self.is_list_empty(list_id):
                raise InvalidMoveException("list is not empty")

            await self.move_to_empty_list(list_id)
