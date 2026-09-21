from datetime import datetime, timedelta
from enum import StrEnum, auto
from typing import Self

from pydantic import AwareDatetime
from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import DateTime, Enum, Index, insert, literal, select, update
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

    @classmethod
    async def add_subscription_days_by_user_id(
        cls, user_id: int, subscription_days: int
    ) -> None:
        current_timestamp = datetime_utc_now()
        target_id = (
            select(cls.id)
            .filter_by(user_id=user_id)
            .filter(cls.ends_at > current_timestamp)
            .order_by(cls.ends_at.desc())
            .limit(1)
            .scalar_subquery()
        )
        updated_subscriptions = (
            update(cls)
            .filter(cls.id == target_id)
            .values(ends_at=cls.ends_at + timedelta(days=subscription_days))
            .returning(cls.id)
            .cte()
        )
        stmt = insert(cls).from_select(
            [cls.user_id, cls.plan_kind, cls.created_at, cls.ends_at],
            select(
                literal(user_id, type_=cls.user_id.type),
                literal(SubscriptionPlanKind.PRO, type_=cls.plan_kind.type),
                literal(current_timestamp, type_=cls.created_at.type),
                literal(
                    current_timestamp + timedelta(days=subscription_days),
                    type_=cls.ends_at.type,
                ),
            ).filter(~select(updated_subscriptions.c.id).exists()),
        )
        await db.session.execute(stmt)
