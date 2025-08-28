from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal
from enum import StrEnum, auto
from typing import Annotated, Any, Self

from pydantic import AwareDatetime, BaseModel, Field
from pydantic_marshals.base import CompositeMarshalModel
from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import Enum, ForeignKey, Select, and_, or_, select
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.config import Base
from app.common.sqlalchemy_ext import db
from app.invoices.models.invoice_items_db import InvoiceItem
from app.invoices.models.invoices_db import Invoice


class PaymentStatus(StrEnum):
    WF_PAYMENT = auto()
    WF_CONFIRMATION = auto()
    CANCELED = auto()
    COMPLETE = auto()


class PaymentType(StrEnum):
    TRANSFER = auto()
    CASH = auto()


class RecipientInvoiceCursorSchema(BaseModel):
    created_at: AwareDatetime
    recipient_invoice_id: int


class RecipientInvoiceSearchRequestSchema(BaseModel):
    cursor: RecipientInvoiceCursorSchema | None = None
    limit: Annotated[int, Field(gt=0, lt=100)] = 12


class TutorInvoiceSearchRequestSchema(RecipientInvoiceSearchRequestSchema):
    # filters
    ...


class StudentInvoiceSearchRequestSchema(RecipientInvoiceSearchRequestSchema):
    # filters
    ...


class DetailedRecipientInvoiceSchema(CompositeMarshalModel):
    invoice: Annotated[Invoice, Invoice.InputSchema]
    items: list[Annotated[InvoiceItem, InvoiceItem.ResponseSchema]]


class DetailedTutorInvoiceSchema(DetailedRecipientInvoiceSchema):
    student_id: int


class DetailedStudentInvoiceSchema(DetailedRecipientInvoiceSchema):
    tutor_id: int


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
    def created_at(self) -> datetime:
        return self.invoice.created_at

    @property
    def tutor_id(self) -> int:
        return self.invoice.tutor_id

    TotalType = Annotated[Decimal, Field(ge=0, decimal_places=2)]

    PatchSchema = MappedModel.create(
        columns=[(total, TotalType), payment_type]
    ).as_patch()
    BaseResponseSchema = MappedModel.create(
        columns=[id, (total, TotalType), status, payment_type],
        properties=[created_at],
    )
    TutorResponseSchema = BaseResponseSchema.extend([student_id])
    StudentResponseSchema = BaseResponseSchema.extend(properties=[tutor_id])

    @classmethod
    def select_after_cursor(
        cls, stmt: Select[Any], cursor: RecipientInvoiceCursorSchema
    ) -> Select[tuple[Any]]:
        return stmt.filter(
            or_(
                Invoice.created_at < cursor.created_at,
                and_(
                    Invoice.created_at == cursor.created_at,
                    cls.id > cursor.recipient_invoice_id,
                ),
            ),
        )

    @classmethod
    async def find_paginated_by_tutor(
        cls,
        tutor_id: int,
        cursor: RecipientInvoiceCursorSchema | None,
        limit: int,
    ) -> Sequence[Self]:
        stmt = select(cls).join(cls.invoice).filter_by(tutor_id=tutor_id)

        if cursor is not None:
            stmt = cls.select_after_cursor(stmt=stmt, cursor=cursor)

        return await db.get_all(
            stmt=stmt.order_by(Invoice.created_at.desc(), cls.id).limit(limit=limit)
        )

    @classmethod
    async def find_paginated_by_student(
        cls, student_id: int, cursor: RecipientInvoiceCursorSchema | None, limit: int
    ) -> Sequence[Self]:
        stmt = select(cls).filter_by(student_id=student_id).join(cls.invoice)

        if cursor is not None:
            stmt = cls.select_after_cursor(stmt=stmt, cursor=cursor)

        return await db.get_all(
            stmt=stmt.order_by(Invoice.created_at.desc(), cls.id).limit(limit=limit)
        )
