from base64 import b32encode
from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, AwareDatetime, Field, PositiveInt
from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import DateTime, String, or_, select, update
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base
from app.common.cyptography import TokenGenerator
from app.common.sqlalchemy_ext import db
from app.common.utils.datetime import datetime_utc_now

promocode_code_generator = TokenGenerator(randomness=8, length=10, encoder=b32encode)


class Promocode(Base):
    __tablename__ = "promocodes"

    @staticmethod
    def generate_code_if_missing(code: str | None) -> str:
        return promocode_code_generator.generate_token() if code is None else code

    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(String(100))
    code: Mapped[str] = mapped_column(String(10), index=True, unique=True)

    valid_from: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    valid_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )

    subscription_days: Mapped[int] = mapped_column()
    usage_limit: Mapped[int | None] = mapped_column(default=None)
    usage_count: Mapped[int] = mapped_column(default=0)
    max_account_age_days: Mapped[int | None] = mapped_column(default=None)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime_utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime_utc_now
    )

    TitleType = Annotated[str, Field(min_length=1, max_length=100)]
    CodeType = Annotated[str, Field(min_length=1, max_length=10)]

    SettingsSchema = MappedModel.create(
        columns=[
            (valid_from, AwareDatetime | None),
            (valid_until, AwareDatetime | None),
            (subscription_days, PositiveInt),
            (usage_limit, PositiveInt | None),
            (max_account_age_days, PositiveInt | None),
        ]
    )
    InputSchema = SettingsSchema.extend(
        columns=[
            (title, TitleType),
            (
                code,
                Annotated[CodeType | None, AfterValidator(generate_code_if_missing)],
            ),
        ]
    )
    UpdateSchema = InputSchema.extend()
    ResponseSchema = InputSchema.extend(
        columns=[
            id,
            (created_at, AwareDatetime),
            (updated_at, AwareDatetime),
            usage_count,
        ]
    )

    @classmethod
    async def is_present_by_code(cls, code: str) -> bool:
        return await db.is_present(select(cls).filter_by(code=code))

    @classmethod
    async def has_incremented_usage_count_by_id(cls, promocode_id: int) -> bool:
        stmt = (
            update(cls)
            .filter_by(id=promocode_id)
            .filter(or_(cls.usage_limit.is_(None), cls.usage_count < cls.usage_limit))
            .values(usage_count=cls.usage_count + 1)
            .returning(cls.id)
        )
        result = await db.session.execute(stmt)
        return result.first() is not None
