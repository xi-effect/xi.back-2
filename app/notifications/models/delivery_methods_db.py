from collections.abc import Sequence
from enum import StrEnum, auto
from typing import Self

from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import BigInteger, Enum, Index, String, and_, select
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base
from app.common.schemas.notifications_sch import DeliveryMethodKind
from app.common.sqlalchemy_ext import db
from app.notifications.models.disabled_delivery_routes_db import (
    DisabledDeliveryRoute,
    NotificationCategory,
)


class DeliveryMethodStatus(StrEnum):
    ACTIVE = auto()
    BLOCKED = auto()
    REPLACED = auto()


class DeliveryMethod(Base):
    __tablename__: str | None = "delivery_methods"

    user_id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[DeliveryMethodKind] = mapped_column(
        Enum(DeliveryMethodKind),
        primary_key=True,
    )

    status: Mapped[DeliveryMethodStatus] = mapped_column(Enum(DeliveryMethodStatus))

    __mapper_args__ = {
        "polymorphic_on": kind,
        "polymorphic_abstract": True,
    }

    ResponseSchema = MappedModel.create(columns=[status])

    @classmethod
    async def find_all_by_user_id(cls, user_id: int) -> Sequence[Self]:
        return await cls.find_all_by_kwargs(user_id=user_id)

    @classmethod
    async def find_first_by_primary_key(
        cls,
        user_id: int,
        kind: DeliveryMethodKind,
    ) -> Self | None:
        return await cls.find_first_by_kwargs(user_id=user_id, kind=kind)

    @classmethod
    async def find_first_by_user_id(cls, user_id: int) -> Self | None:
        if cls is DeliveryMethod:
            raise NotImplementedError
        return await cls.find_first_by_kwargs(user_id=user_id)

    @classmethod
    async def find_first_active_by_delivery_route(
        cls,
        user_id: int,
        notification_category: NotificationCategory | None,
    ) -> Self | None:
        if cls is DeliveryMethod:
            raise NotImplementedError

        stmt = select(cls).filter_by(
            user_id=user_id,
            status=DeliveryMethodStatus.ACTIVE,
        )
        if notification_category is not None:
            stmt = stmt.filter(
                ~select(DisabledDeliveryRoute)
                .filter(
                    DisabledDeliveryRoute.delivery_method_kind == cls.kind,
                    DisabledDeliveryRoute.user_id == cls.user_id,
                    DisabledDeliveryRoute.notification_category
                    == notification_category,
                )
                .exists()
            )
        return await db.get_first(stmt)


class EmailDeliveryMethod(DeliveryMethod):
    __tablename__ = None

    __mapper_args__ = {
        "polymorphic_identity": DeliveryMethodKind.EMAIL,
        "polymorphic_load": "inline",
    }

    email: Mapped[str] = mapped_column(String(100), index=True, nullable=True)

    InputSchema = MappedModel.create(columns=[(email, str)])


class MessengerDeliveryMethod(DeliveryMethod):
    __tablename__ = None
    __mapper_args__ = {
        "polymorphic_abstract": True,
    }

    peer_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=True)

    @classmethod
    async def find_first_by_peer_id_and_status(
        cls,
        peer_id: int,
        allowed_statuses: list[DeliveryMethodStatus],
    ) -> Self | None:
        stmt = (
            select(cls)
            .filter_by(peer_id=peer_id)
            .filter(cls.status.in_(allowed_statuses))
        )
        return await db.get_first(stmt)


class TelegramDeliveryMethod(MessengerDeliveryMethod):
    __tablename__ = None

    __mapper_args__ = {
        "polymorphic_identity": DeliveryMethodKind.TELEGRAM,
        "polymorphic_load": "inline",
    }


class VKDeliveryMethod(MessengerDeliveryMethod):
    __tablename__ = None

    __mapper_args__ = {
        "polymorphic_identity": DeliveryMethodKind.VK,
        "polymorphic_load": "inline",
    }


# declared outside the class, because STI doesn't support indexes on child classes
Index(
    "unique_index_delivery_methods_active_or_blocked_peer_id",
    MessengerDeliveryMethod.kind,
    MessengerDeliveryMethod.peer_id,
    postgresql_where=and_(
        MessengerDeliveryMethod.kind.in_(
            (DeliveryMethodKind.TELEGRAM, DeliveryMethodKind.VK)
        ),
        MessengerDeliveryMethod.status.in_(
            (DeliveryMethodStatus.ACTIVE, DeliveryMethodStatus.BLOCKED)
        ),
    ),
    unique=True,
)
