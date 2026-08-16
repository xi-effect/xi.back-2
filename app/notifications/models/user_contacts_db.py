from collections.abc import Iterable, Sequence
from typing import Self

from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import Enum, String, Text, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base
from app.common.schemas.user_contacts_sch import UserContactKind
from app.common.sqlalchemy_ext import db


class UserContact(Base):
    __tablename__ = "user_contacts"

    user_id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[UserContactKind] = mapped_column(
        Enum(UserContactKind, name="contactkind"), primary_key=True
    )

    link: Mapped[str] = mapped_column(Text)
    title: Mapped[str] = mapped_column(String(100))

    is_public: Mapped[bool] = mapped_column()

    InputSchema = MappedModel.create(columns=[link, title, is_public])
    PublicSchema = MappedModel.create(columns=[kind, link, title])
    ResponseSchema = InputSchema.extend()
    FullSchema = PublicSchema.extend(columns=[is_public])

    @classmethod
    async def find_all_by_user_id_and_kinds(
        cls,
        user_id: int,
        allowed_kinds: Iterable[UserContactKind],
    ) -> Sequence[Self]:
        return await db.get_all(
            select(cls).filter_by(user_id=user_id).filter(cls.kind.in_(allowed_kinds))
        )

    @classmethod
    async def find_all_by_user_id(
        cls,
        user_id: int,
        public_only: bool = False,
    ) -> Sequence[Self]:
        if public_only:
            return await cls.find_all_by_kwargs(user_id=user_id, is_public=True)
        return await cls.find_all_by_kwargs(user_id=user_id)

    @classmethod
    async def find_first_by_primary_key(
        cls,
        user_id: int,
        kind: UserContactKind,
    ) -> Self | None:
        return await cls.find_first_by_kwargs(user_id=user_id, kind=kind)

    @classmethod
    async def upsert(
        cls,
        user_id: int,
        kind: UserContactKind,
        link: str,
        title: str,
    ) -> Self:
        stmt = (
            insert(cls)
            .values(
                user_id=user_id,
                kind=kind,
                link=link,
                title=title,
                is_public=True,
            )
            .on_conflict_do_update(
                set_={
                    "link": link,
                    "title": title,
                },
                index_elements=["user_id", "kind"],
            )
            .returning(cls)
        )
        return (await db.session.execute(stmt)).scalar_one()

    @classmethod
    async def delete_by_primary_key(
        cls,
        user_id: int,
        kind: UserContactKind,
    ) -> None:
        await cls.delete_by_kwargs(user_id=user_id, kind=kind)
