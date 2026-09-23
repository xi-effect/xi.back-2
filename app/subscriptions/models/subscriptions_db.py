from datetime import datetime
from enum import StrEnum, auto

from pydantic import AwareDatetime
from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base


class SubscriptionPlanKind(StrEnum):
    PRO = auto()


class Subscription(Base):
    __tablename__ = "subscriptions"

    user_id: Mapped[int] = mapped_column(primary_key=True)

    plan_kind: Mapped[SubscriptionPlanKind] = mapped_column(Enum(SubscriptionPlanKind))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    ResponseSchema = MappedModel.create(columns=[plan_kind, (ends_at, AwareDatetime)])
