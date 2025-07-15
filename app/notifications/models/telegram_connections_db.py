from enum import StrEnum, auto
from typing import Self

from sqlalchemy import BigInteger, Enum, select
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base
from app.common.sqlalchemy_ext import db


class TelegramConnectionStatus(StrEnum):
    ACTIVE = auto()
    BLOCKED = auto()
    REPLACED = auto()


class TelegramConnection(Base):
    __tablename__ = "telegram_connections"

    user_id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, index=True)
    status: Mapped[TelegramConnectionStatus] = mapped_column(
        Enum(TelegramConnectionStatus)
    )

    @classmethod
    async def find_first_by_user_id_and_status(
        cls, user_id: int, allowed_statuses: list[TelegramConnectionStatus]
    ) -> Self | None:
        stmt = (
            select(cls)
            .filter_by(user_id=user_id)
            .filter(cls.status.in_(allowed_statuses))
        )
        return await db.get_first(stmt)

    @classmethod
    async def find_first_by_chat_id_and_status(
        cls, chat_id: int, allowed_statuses: list[TelegramConnectionStatus]
    ) -> Self | None:
        stmt = (
            select(cls)
            .filter_by(chat_id=chat_id)
            .filter(cls.status.in_(allowed_statuses))
        )
        return await db.get_first(stmt)
