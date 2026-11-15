from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal
from enum import StrEnum, auto
from typing import Annotated, Any, Self

from pydantic import AwareDatetime, BaseModel, Field, model_validator
from pydantic_marshals.base import CompositeMarshalModel
from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import Enum, ForeignKey, Select, and_, or_, select
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.config import Base
from app.common.sqlalchemy_ext import db
from app.invoices.models.invoice_items_db import InvoiceItem
from app.invoices.models.invoices_db import Invoice


class PaymentStatus(StrEnum):
    WF_SENDER_CONFIRMATION = auto()
    WF_RECEIVER_CONFIRMATION = auto()
    COMPLETE = auto()


class PaymentType(StrEnum):
    TRANSFER = auto()
    CASH = auto()


class RecipientInvoiceCursorSchema(BaseModel):
    created_at: AwareDatetime
    recipient_invoice_id: int


class RecipientInvoiceFiltersSchema(BaseModel):
    status__in: Annotated[
        set[PaymentStatus] | None,
        Field(min_length=1, max_length=len(PaymentStatus)),
    ] = None
    payment_type__in: Annotated[
        set[PaymentType | None] | None,
        Field(min_length=1, max_length=len(PaymentType) + 1),
    ] = None
    created_at__ge: AwareDatetime | None = None
    created_at__lt: AwareDatetime | None = None
    total__ge: Annotated[Decimal, Field(ge=0, decimal_places=2)] | None = None
    total__le: Annotated[Decimal, Field(ge=0, decimal_places=2)] | None = None

    @model_validator(mode="after")
    def validate_created_at_range(self) -> Self:
        if (
            self.created_at__ge is not None
            and self.created_at__lt is not None
            and self.created_at__ge >= self.created_at__lt
        ):
            raise ValueError("created_at__lt must be later in time than created_at__ge")
        return self

    @model_validator(mode="after")
    def validate_total_range(self) -> Self:
        if (
            self.total__ge is not None
            and self.total__le is not None
            and self.total__ge > self.total__le
        ):
            raise ValueError("total__le must be greater than or equal to total__ge")
        return self


class TutorInvoiceFiltersSchema(RecipientInvoiceFiltersSchema):
    student_id__in: Annotated[set[int] | None, Field(min_length=1, max_length=20)] = (
        None
    )


class StudentInvoiceFiltersSchema(RecipientInvoiceFiltersSchema):
    tutor_id__in: Annotated[set[int] | None, Field(min_length=1, max_length=20)] = None


class RecipientInvoiceSearchRequestSchema(BaseModel):
    cursor: RecipientInvoiceCursorSchema | None = None
    limit: Annotated[int, Field(gt=0, lt=100)] = 12


class TutorInvoiceSearchRequestSchema(RecipientInvoiceSearchRequestSchema):
    filters: TutorInvoiceFiltersSchema = Field(
        default_factory=TutorInvoiceFiltersSchema
    )


class StudentInvoiceSearchRequestSchema(RecipientInvoiceSearchRequestSchema):
    filters: StudentInvoiceFiltersSchema = Field(
        default_factory=StudentInvoiceFiltersSchema
    )


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

    @property
    def classroom_id(self) -> int:
        return self.invoice.classroom_id

    TotalType = Annotated[Decimal, Field(ge=0, decimal_places=2)]

    PatchSchema = MappedModel.create(
        columns=[(total, TotalType), payment_type]
    ).as_patch()
    PaymentSchema = MappedModel.create(columns=[(payment_type, PaymentType)])
    ResponseSchema = MappedModel.create(
        columns=[(total, TotalType), status, payment_type]
    )
    BaseFullResponseSchema = MappedModel.create(
        columns=[id, (total, TotalType), status, payment_type],
        properties=[created_at, classroom_id],
    )
    TutorResponseSchema = BaseFullResponseSchema.extend(columns=[student_id])
    StudentResponseSchema = BaseFullResponseSchema.extend(properties=[tutor_id])

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
    def select_by_search_params(
        cls,
        search_params: (
            TutorInvoiceSearchRequestSchema | StudentInvoiceSearchRequestSchema
        ),
    ) -> Select[tuple[Self]]:
        stmt = select(cls).join(cls.invoice)

        if search_params.filters.status__in is not None:
            stmt = stmt.filter(cls.status.in_(search_params.filters.status__in))

        if search_params.filters.payment_type__in is not None:
            payment_type_conditions = []
            payment_types = search_params.filters.payment_type__in - {None}
            if len(payment_types) != 0:
                payment_type_conditions.append(cls.payment_type.in_(payment_types))
            if None in search_params.filters.payment_type__in:
                payment_type_conditions.append(cls.payment_type.is_(None))
            stmt = stmt.filter(or_(*payment_type_conditions))

        if search_params.filters.created_at__ge is not None:
            stmt = stmt.filter(
                Invoice.created_at >= search_params.filters.created_at__ge
            )

        if search_params.filters.created_at__lt is not None:
            stmt = stmt.filter(
                Invoice.created_at < search_params.filters.created_at__lt
            )

        if search_params.filters.total__ge is not None:
            stmt = stmt.filter(cls.total >= search_params.filters.total__ge)

        if search_params.filters.total__le is not None:
            stmt = stmt.filter(cls.total <= search_params.filters.total__le)

        if search_params.cursor is not None:
            stmt = cls.select_after_cursor(stmt=stmt, cursor=search_params.cursor)

        return stmt.order_by(Invoice.created_at.desc(), cls.id).limit(
            search_params.limit
        )

    @classmethod
    async def find_paginated_by_tutor_id(
        cls,
        tutor_id: int,
        search_params: TutorInvoiceSearchRequestSchema,
        classroom_id: int | None = None,
    ) -> Sequence[Self]:
        stmt = cls.select_by_search_params(search_params).filter(
            Invoice.tutor_id == tutor_id
        )

        if classroom_id is not None:
            stmt = stmt.filter(Invoice.classroom_id == classroom_id)

        if search_params.filters.student_id__in is not None:
            stmt = stmt.filter(cls.student_id.in_(search_params.filters.student_id__in))

        return await db.get_all(stmt)

    @classmethod
    async def find_paginated_by_student_id(
        cls,
        student_id: int,
        search_params: StudentInvoiceSearchRequestSchema,
        classroom_id: int | None = None,
    ) -> Sequence[Self]:
        stmt = cls.select_by_search_params(search_params).filter(
            cls.student_id == student_id
        )

        if classroom_id is not None:
            stmt = stmt.filter(Invoice.classroom_id == classroom_id)

        if search_params.filters.tutor_id__in is not None:
            stmt = stmt.filter(Invoice.tutor_id.in_(search_params.filters.tutor_id__in))

        return await db.get_all(stmt)


class DetailedRecipientInvoiceSchema(CompositeMarshalModel):
    invoice: Annotated[Invoice, Invoice.BaseResponseSchema]
    recipient_invoice: Annotated[RecipientInvoice, RecipientInvoice.ResponseSchema]
    invoice_items: list[Annotated[InvoiceItem, InvoiceItem.InputSchema]]


class DetailedTutorRecipientInvoiceSchema(DetailedRecipientInvoiceSchema):
    student_id: int


class DetailedStudentRecipientInvoiceSchema(DetailedRecipientInvoiceSchema):
    tutor_id: int
