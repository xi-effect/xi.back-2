from __future__ import annotations

import asyncio
import sys
from collections.abc import Sequence
from contextvars import ContextVar
from typing import Any, Self

from sqlalchemy import Row, Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

session_context: ContextVar[AsyncSession | None] = ContextVar("session", default=None)


class DBController:
    @property
    def session(self) -> AsyncSession:
        """Return an instance of Session local to the current context"""
        session = session_context.get()
        if session is None:
            raise ValueError("Session not initialized")
        return session

    async def get_first_row(self, stmt: Select[Any]) -> Row[Any] | None:
        return (await self.session.execute(stmt)).first()

    async def get_first(self, stmt: Select[Any]) -> Any | None:
        return (await self.session.execute(stmt)).scalars().first()

    async def is_absent(self, stmt: Select[Any]) -> bool:
        return (await self.get_first(stmt)) is None

    async def is_present(self, stmt: Select[Any]) -> bool:
        return not await self.is_absent(stmt)

    async def get_count(self, stmt: Select[tuple[int]]) -> int:
        return (await self.session.execute(stmt)).scalar_one()

    async def get_all(self, stmt: Select[Any]) -> Sequence[Any]:
        return (await self.session.execute(stmt)).scalars().all()

    async def get_paginated(
        self, stmt: Select[Any], offset: int, limit: int
    ) -> Sequence[Any]:
        return await self.get_all(stmt.offset(offset).limit(limit))


db: DBController = DBController()


class MappingBase:
    @classmethod
    async def create(cls, **kwargs: Any) -> Self:
        entry = cls(**kwargs)  # noqa
        db.session.add(entry)
        await db.session.flush()
        return entry

    @classmethod
    def select_by_kwargs(cls, *order_by: Any, **kwargs: Any) -> Select[tuple[Self]]:
        if len(order_by) == 0:
            return select(cls).filter_by(**kwargs)
        return select(cls).filter_by(**kwargs).order_by(*order_by)

    @classmethod
    async def find_first_by_id(cls, *keys: Any) -> Self | None:
        return await db.session.get(cls, *keys)

    @classmethod
    async def find_first_by_kwargs(cls, *order_by: Any, **kwargs: Any) -> Self | None:
        return await db.get_first(cls.select_by_kwargs(*order_by, **kwargs))

    @classmethod
    async def find_all_by_kwargs(cls, *order_by: Any, **kwargs: Any) -> Sequence[Self]:
        return await db.get_all(cls.select_by_kwargs(*order_by, **kwargs))

    @classmethod
    async def find_paginated_by_kwargs(
        cls,
        offset: int,
        limit: int,
        *order_by: Any,
        **kwargs: Any,
    ) -> Sequence[Self]:
        return await db.get_paginated(
            cls.select_by_kwargs(*order_by, **kwargs),
            offset=offset,
            limit=limit,
        )

    @classmethod
    async def count_by_kwargs(cls, *expressions: Any, **kwargs: Any) -> int:
        return await db.get_count(select(func.count(*expressions)).filter_by(**kwargs))

    def update(self, **kwargs: Any) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)

    async def delete(self) -> None:
        await db.session.delete(self)
        await db.session.flush()


sqlalchemy_naming_convention = {
    "ix": "ix_%(column_0_label)s",  # noqa: WPS323
    "uq": "uq_%(table_name)s_%(column_0_name)s",  # noqa: WPS323
    "ck": "ck_%(table_name)s_%(constraint_name)s",  # noqa: WPS323
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",  # noqa: WPS323
    "pk": "pk_%(table_name)s",  # noqa: WPS323
}
