from typing import Self

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base
from app.common.sqlalchemy_ext import db
from app.users.models.user_flag_kinds_db import UserFlagKind
from app.users.models.users_db import User


class UserFlag(Base):
    __tablename__ = "user_flags"

    user_id: Mapped[int] = mapped_column(
        ForeignKey(User.id, ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    user_flag_kind_id: Mapped[int] = mapped_column(
        ForeignKey(UserFlagKind.id, ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )

    value: Mapped[bool] = mapped_column()

    @classmethod
    async def find_first_by_primary_key(
        cls,
        user_id: int,
        user_flag_kind_id: int,
    ) -> Self | None:
        return await cls.find_first_by_kwargs(
            user_id=user_id,
            user_flag_kind_id=user_flag_kind_id,
        )

    @classmethod
    async def upsert(cls, user_id: int, user_flag_kind_id: int, value: bool) -> None:
        stmt = (
            insert(cls)
            .values(
                user_id=user_id,
                user_flag_kind_id=user_flag_kind_id,
                value=value,
            )
            .on_conflict_do_update(
                set_={"value": value},
                index_elements=["user_id", "user_flag_kind_id"],
            )
        )
        await db.session.execute(stmt)
