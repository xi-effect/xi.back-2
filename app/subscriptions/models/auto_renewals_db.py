from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base
from app.subscriptions.schemas.subscriptions_sch import SubscriptionPeriod


class AutoRenewal(Base):
    __tablename__ = "auto_renewals"

    user_id: Mapped[int] = mapped_column(primary_key=True)

    provider_payment_method_id: Mapped[str] = mapped_column(String(50))
    renewal_period: Mapped[SubscriptionPeriod] = mapped_column(Enum(SubscriptionPeriod))

    ResponseSchema = MappedModel.create(columns=[renewal_period])
