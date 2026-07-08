from base64 import b32encode
from datetime import datetime
from typing import Annotated

from pydantic import AwareDatetime, Field
from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import DateTime, String, select
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base
from app.common.cyptography import TokenGenerator
from app.common.sqlalchemy_ext import db
from app.common.utils.datetime import datetime_utc_now

promocode_code_generator = TokenGenerator(randomness=8, length=10, encoder=b32encode)


class Promocode(Base):
    __tablename__ = "promocodes"

    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(String(100))
    code: Mapped[str] = mapped_column(
        String(10),
        index=True,
        unique=True,
        default=promocode_code_generator.generate_token,
    )

    valid_from: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    valid_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime_utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime_utc_now
    )

    TitleType = Annotated[str, Field(min_length=1, max_length=100)]
    CodeType = Annotated[str, Field(min_length=1, max_length=10)]

    ValidityPeriodInputSchema = MappedModel.create(
        columns=[
            (valid_from, AwareDatetime | None),
            (valid_until, AwareDatetime | None),
        ]
    )
    InputSchema = ValidityPeriodInputSchema.extend(
        columns=[
            (title, TitleType),
            (code, CodeType | None),
        ]
    )
    UpdateSchema = ValidityPeriodInputSchema.extend(
        columns=[
            (title, TitleType),
            (code, CodeType),
        ]
    )
    ResponseSchema = InputSchema.extend(
        columns=[id, (created_at, AwareDatetime), (updated_at, AwareDatetime)]
    )

    @classmethod
    async def is_present_by_code(cls, code: str) -> bool:
        return await db.is_present(select(cls).filter_by(code=code))
