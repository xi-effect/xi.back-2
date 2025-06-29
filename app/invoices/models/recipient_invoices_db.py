from enum import StrEnum, auto

from sqlalchemy import Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base
from app.invoices.models.invoices_db import Invoice


class PaymentStatus(StrEnum):
    WF_PAYMENT = auto()
    WF_CONFIRMATION = auto()
    CANCELED = auto()
    COMPLETE = auto()


class RecipientInvoice(Base):
    __tablename__ = "recipient_invoices"

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(
        ForeignKey(Invoice.id, ondelete="CASCADE"),
        index=True,
    )

    recipient_user_id: Mapped[int] = mapped_column(index=True)
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus))
