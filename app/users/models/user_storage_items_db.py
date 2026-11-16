from typing import Annotated, ClassVar, Self

from pydantic import Field, JsonValue, TypeAdapter
from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base
from app.common.sqlalchemy_ext import db
from app.users.models.users_db import User

json_value_type_adapter: TypeAdapter[JsonValue] = TypeAdapter(JsonValue)


class UserStorageItem(Base):
    __tablename__ = "user_storage_items"

    max_value_size_bytes: ClassVar[int] = 64 * 1024

    user_id: Mapped[int] = mapped_column(
        ForeignKey(User.id, ondelete="CASCADE"),
        primary_key=True,
    )
    key: Mapped[str] = mapped_column(String(100), primary_key=True)

    value: Mapped[JsonValue] = mapped_column(JSON, nullable=False)

    KeyType = Annotated[str, Field(min_length=1, max_length=100)]

    @classmethod
    def is_value_too_large(cls, value: JsonValue) -> bool:
        return len(json_value_type_adapter.dump_json(value)) > cls.max_value_size_bytes

    @classmethod
    async def find_first_by_primary_key(
        cls,
        user_id: int,
        key: str,
    ) -> Self | None:
        return await cls.find_first_by_kwargs(user_id=user_id, key=key)

    @classmethod
    async def upsert(cls, user_id: int, key: str, value: JsonValue) -> None:
        stmt = (
            insert(cls)
            .values(user_id=user_id, key=key, value=value)
            .on_conflict_do_update(
                set_={"value": value},
                index_elements=["user_id", "key"],
            )
        )
        await db.session.execute(stmt)
