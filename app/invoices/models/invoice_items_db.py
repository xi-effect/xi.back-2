from decimal import Decimal
from typing import Annotated

from pydantic import Field
from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base
from app.invoices.models.invoices_db import Invoice


class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(
        ForeignKey(Invoice.id, ondelete="CASCADE"),
        index=True,
    )
    position: Mapped[int] = mapped_column()

    name: Mapped[str] = mapped_column(String(100))
    price: Mapped[Decimal] = mapped_column()
    quantity: Mapped[int] = mapped_column()

    NameType = Annotated[str, Field(min_length=1, max_length=100)]
    PriceType = Annotated[Decimal, Field(ge=0, decimal_places=2)]
    QuantityType = Annotated[int, Field(lt=1000, gt=0)]

    InputSchema = MappedModel.create(
        columns=[
            (name, NameType),
            (price, PriceType),
            (quantity, QuantityType),
        ]
    )
    ResponseSchema = InputSchema.extend(columns=[id])
