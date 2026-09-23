from datetime import datetime

from pydantic import AwareDatetime
from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base
from app.common.schemas.subscriptions_sch import PaidPlanKind


class Subscription(Base):
    __tablename__ = "subscriptions"

    user_id: Mapped[int] = mapped_column(primary_key=True)

    plan_kind: Mapped[PaidPlanKind] = mapped_column(Enum(PaidPlanKind))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    ResponseSchema = MappedModel.create(columns=[plan_kind, (ends_at, AwareDatetime)])
