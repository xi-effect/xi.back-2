from collections.abc import Sequence
from enum import StrEnum
from typing import Self

from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base


class ContactKind(StrEnum):
    PERSONAL_TELEGRAM = "personal-telegram"


class UserContact(Base):
    __tablename__ = "user_contacts"

    user_id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[ContactKind] = mapped_column(Enum(ContactKind), primary_key=True)

    link: Mapped[str] = mapped_column(Text)
    title: Mapped[str] = mapped_column(String(100))

    is_public: Mapped[bool] = mapped_column()

    InputSchema = MappedModel.create(columns=[link, title, is_public])
    PublicSchema = MappedModel.create(columns=[kind, link, title])
    ResponseSchema = InputSchema.extend()
    FullSchema = PublicSchema.extend(columns=[is_public])

    @classmethod
    async def find_first_by_primary_key(
        cls, user_id: int, kind: ContactKind
    ) -> Self | None:
        return await cls.find_first_by_kwargs(user_id=user_id, kind=kind)

    @classmethod
    async def find_all_by_user(
        cls, user_id: int, public_only: bool = False
    ) -> Sequence[Self]:
        if public_only:
            return await cls.find_all_by_kwargs(user_id=user_id, is_public=True)
        return await cls.find_all_by_kwargs(user_id=user_id)
