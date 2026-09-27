from datetime import datetime
from typing import Self
from uuid import UUID, uuid4

from pydantic import AwareDatetime
from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import DateTime, String, select, update
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base
from app.common.sqlalchemy_ext import db
from app.common.utils.datetime import datetime_utc_now


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    provider_payment_id: Mapped[str] = mapped_column(
        String(50), index=True, unique=True
    )
    user_id: Mapped[int] = mapped_column(index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime_utc_now
    )
    amount_roubles: Mapped[int] = mapped_column()
    subscription_days: Mapped[int] = mapped_column()

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    cancellation_reason: Mapped[str | None] = mapped_column(String(100), default=None)

    ResponseSchema = MappedModel.create(
        columns=[
            id,
            provider_payment_id,
            (created_at, AwareDatetime),
            amount_roubles,
            subscription_days,
            (completed_at, AwareDatetime | None),
            cancellation_reason,
        ]
    )

    @classmethod
    async def is_present_by_id(cls, payment_id: UUID) -> bool:
        return await db.is_present(select(cls).filter_by(id=payment_id))

    @classmethod
    async def find_and_complete_by_id(
        cls,
        payment_id: UUID,
        cancellation_reason: str | None = None,
    ) -> Self | None:
        stmt = (
            update(cls)
            .filter_by(id=payment_id)
            .filter(cls.completed_at.is_(None))
            .values(
                completed_at=datetime_utc_now(),
                cancellation_reason=cancellation_reason,
            )
            .returning(cls)
        )
        return (await db.session.execute(stmt)).scalar_one_or_none()
