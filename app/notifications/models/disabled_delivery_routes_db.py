from collections.abc import Sequence
from enum import StrEnum, auto
from typing import Self

from sqlalchemy import Enum, delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base
from app.common.schemas.notifications_sch import DeliveryMethodKind
from app.common.sqlalchemy_ext import db


class NotificationCategory(StrEnum):
    CLASSROOMS = auto()
    INVOICES = auto()
    EVENTS = auto()
    EVENT_REMINDERS = auto()


class DisabledDeliveryRoute(Base):
    __tablename__ = "disabled_delivery_routes"

    user_id: Mapped[int] = mapped_column(primary_key=True, index=True)
    delivery_method_kind: Mapped[DeliveryMethodKind] = mapped_column(
        Enum(DeliveryMethodKind),
        primary_key=True,
    )
    notification_category: Mapped[NotificationCategory] = mapped_column(
        Enum(NotificationCategory),
        primary_key=True,
    )

    @classmethod
    async def find_all_by_user_id(cls, user_id: int) -> Sequence[Self]:
        return await cls.find_all_by_kwargs(user_id=user_id)

    @classmethod
    async def disable_by_primary_key(
        cls,
        user_id: int,
        delivery_method_kind: DeliveryMethodKind,
        notification_category: NotificationCategory,
    ) -> None:
        await db.session.execute(
            insert(cls)
            .values(
                user_id=user_id,
                delivery_method_kind=delivery_method_kind,
                notification_category=notification_category,
            )
            .on_conflict_do_nothing()
        )

    @classmethod
    async def enable_by_primary_key(
        cls,
        user_id: int,
        delivery_method_kind: DeliveryMethodKind,
        notification_category: NotificationCategory,
    ) -> None:
        await db.session.execute(
            delete(cls).filter_by(
                user_id=user_id,
                delivery_method_kind=delivery_method_kind,
                notification_category=notification_category,
            )
        )
