from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal
from enum import StrEnum, auto
from typing import Any, Self

from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import Enum, ForeignKey, select
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.config import Base
from app.common.sqlalchemy_ext import db
from app.invoices.models.invoices_db import Invoice


class PaymentStatus(StrEnum):
    WF_PAYMENT = auto()
    WF_CONFIRMATION = auto()
    CANCELED = auto()
    COMPLETE = auto()


class PaymentType(StrEnum):
    TRANSFER = auto()
    CASH = auto()


class RecipientInvoice(Base):
    __tablename__ = "recipient_invoices"

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(
        ForeignKey(Invoice.id, ondelete="CASCADE"),
        index=True,
    )
    invoice: Mapped[Invoice] = relationship(lazy="joined")

    student_id: Mapped[int] = mapped_column(index=True)
    total: Mapped[Decimal] = mapped_column()

    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus))
    payment_type: Mapped[PaymentType | None] = mapped_column(
        Enum(PaymentType), default=None
    )

    @property
    def tutor_id(self) -> int:
        return self.invoice.tutor_id

    @property
    def created_at(self) -> datetime:
        return self.invoice.created_at

    @classmethod
    async def find_paginated_by_criteria(
        cls,
        offset: int,
        limit: int,
        *criteria: Any,
        order_by_one: Any | None = None,
        **kwargs: Any,
    ) -> Sequence[Self]:
        stmt = select(cls).filter(*criteria).filter_by(**kwargs)
        if order_by_one is None:
            stmt = stmt.order_by(order_by_one)
        return await db.get_paginated(stmt, offset, limit)

    PatchSchema = MappedModel.create(columns=[total, payment_type]).as_patch()

    BaseResponseSchema = MappedModel.create(
        columns=[total, status, payment_type], properties=[created_at]
    )
    TutorResponseSchema = BaseResponseSchema.extend([student_id])
