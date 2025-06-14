from datetime import datetime

from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    tutor_id: Mapped[int] = mapped_column()
    student_id: Mapped[int] = mapped_column()
    payed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=None)
    amount: Mapped[int] = mapped_column()

    InputSchema = MappedModel.create(columns=[student_id, payed_at, amount])
    PatchSchema = MappedModel.create(columns=[tutor_id, payed_at, amount])
    ResponseSchema = MappedModel.create(
        columns=[id, tutor_id, student_id, payed_at, amount]
    )

    __table_args__ = (Index("payments_tutor_payed_at_index", "tutor_id", "payed_at"),)
