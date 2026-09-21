from datetime import datetime
from enum import StrEnum, auto
from typing import Self

from pydantic import AwareDatetime
from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import DateTime, Enum, Index, select
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base
from app.common.sqlalchemy_ext import db
from app.common.utils.datetime import datetime_utc_now


class SubscriptionPlanKind(StrEnum):
    PRO = auto()


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column()

    plan_kind: Mapped[SubscriptionPlanKind] = mapped_column(Enum(SubscriptionPlanKind))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime_utc_now
    )
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    __table_args__ = (Index("index_subscriptions_user_id_ends_at", user_id, ends_at),)

    ResponseSchema = MappedModel.create(columns=[plan_kind, (ends_at, AwareDatetime)])

    @classmethod
    async def find_active_by_user_id(cls, user_id: int) -> Self | None:
        return await db.get_first(
            select(cls)
            .filter(cls.ends_at > datetime_utc_now())
            .filter_by(user_id=user_id)
            .order_by(cls.ends_at.desc())
        )
