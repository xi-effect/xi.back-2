from datetime import datetime
from typing import Self

from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base


class Payment(Base):
    __tablename__ = "history_payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    tutor_id: Mapped[int] = mapped_column()
    student_id: Mapped[int] = mapped_column()
    payed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    amount: Mapped[int] = mapped_column()

    InputSchema = MappedModel.create(columns=[tutor_id, student_id, payed_at, amount])
    PatchSchema = InputSchema.as_patch()
    ResponseSchema = InputSchema.extend(columns=[id])

    @classmethod
    async def find_or_create(
        cls,
        tutor_id: int,
        student_id: int,
        payed_at: datetime,
        amount: int,
    ) -> Self:
        payment = await cls.find_first_by_kwargs(
            tutor_id=tutor_id,
            student_id=student_id,
            payed_at=payed_at,
            amount=amount,
        )
        if payment is None:
            return await cls.create(
                tutor_id=tutor_id,
                student_id=student_id,
                payed_at=payed_at,
                amount=amount,
            )
        return payment
