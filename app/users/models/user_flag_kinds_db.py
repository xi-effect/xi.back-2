from typing import Annotated

from pydantic import Field
from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import String, select
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base
from app.common.sqlalchemy_ext import db


class UserFlagKind(Base):
    __tablename__ = "user_flag_kinds"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(100), index=True, unique=True)
    default_value: Mapped[bool] = mapped_column(default=False)

    KeyType = Annotated[str, Field(min_length=1, max_length=100)]

    InputSchema = MappedModel.create(columns=[(key, KeyType), default_value])
    PatchSchema = InputSchema.as_patch()
    ResponseSchema = InputSchema.extend(columns=[id])

    @classmethod
    async def is_present_by_key(cls, key: str) -> bool:
        return await db.is_present(select(cls).filter_by(key=key))
