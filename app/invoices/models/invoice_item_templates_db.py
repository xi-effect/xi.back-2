from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal
from typing import Annotated, ClassVar, Self

from pydantic import Field
from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import DateTime, String, select
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base
from app.common.sqlalchemy_ext import db
from app.common.utils.datetime import datetime_utc_now


class InvoiceItemTemplate(Base):
    __tablename__ = "invoice_item_templates"

    max_count_per_user: ClassVar[int] = 20

    id: Mapped[int] = mapped_column(primary_key=True)
    creator_user_id: Mapped[int] = mapped_column(index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime_utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime_utc_now
    )

    name: Mapped[str] = mapped_column(String(100))
    price: Mapped[Decimal] = mapped_column()

    NameType = Annotated[str, Field(min_length=1, max_length=100)]
    PriceType = Annotated[Decimal, Field(ge=0, decimal_places=2)]

    InputSchema = MappedModel.create(
        columns=[
            (name, NameType),
            (price, PriceType),
        ]
    )
    PatchSchema = InputSchema.as_patch()
    ResponseSchema = InputSchema.extend(columns=[id, created_at, updated_at])

    @classmethod
    async def is_limit_per_user_reached(cls, user_id: int) -> bool:
        return (
            await cls.count_by_kwargs(cls.id, creator_user_id=user_id)
            >= cls.max_count_per_user
        )

    @classmethod
    async def find_all_by_creator(cls, creator_user_id: int) -> Sequence[Self]:
        stmt = select(cls).filter_by(creator_user_id=creator_user_id)
        return await db.get_all(stmt=stmt.order_by(cls.updated_at.desc()))
