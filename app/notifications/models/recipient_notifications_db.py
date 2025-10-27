from collections.abc import Sequence
from datetime import datetime
from typing import Self
from uuid import UUID

from pydantic import AwareDatetime
from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import DateTime, ForeignKey, select
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.functions import count

from app.common.config import Base
from app.common.sqlalchemy_ext import db
from app.common.utils.datetime import datetime_utc_now
from app.notifications.models.notifications_db import (
    Notification,
    NotificationSearchRequestSchema,
)


class RecipientNotification(Base):
    __tablename__ = "recipient_notifications"

    notification_id: Mapped[UUID] = mapped_column(
        ForeignKey(Notification.id, ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    notification: Mapped[Notification] = relationship(lazy="joined")
    recipient_user_id: Mapped[int] = mapped_column(primary_key=True, index=True)

    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    ResponseSchema = MappedModel.create(
        columns=[(read_at, AwareDatetime | None)],
        relationships=[(notification, Notification.ResponseSchema)],
    )

    @classmethod
    async def find_paginated_by_recipient_user_id(
        cls,
        recipient_user_id: int,
        search_params: NotificationSearchRequestSchema,
    ) -> Sequence[Self]:
        stmt = (
            select(cls)
            .filter_by(recipient_user_id=recipient_user_id)
            .join(Notification)
            .order_by(Notification.created_at.desc())
        )

        if search_params.cursor is not None:
            stmt = stmt.filter(
                Notification.created_at < search_params.cursor.created_at
            )

        return await db.get_all(stmt=stmt.limit(search_params.limit))

    @classmethod
    async def count_unread_by_recipient_user_id(
        cls,
        recipient_user_id: int,
        limit: int,
    ) -> int:
        stmt = (
            select(cls.notification_id)
            .filter_by(recipient_user_id=recipient_user_id)
            .filter(cls.read_at.is_(None))
            .limit(limit)
        )
        return await db.get_count(select(count()).select_from(stmt.subquery()))

    @classmethod
    async def find_first_by_ids(
        cls,
        notification_id: UUID,
        recipient_user_id: int,
    ) -> Self | None:
        return await cls.find_first_by_kwargs(
            notification_id=notification_id,
            recipient_user_id=recipient_user_id,
        )

    def mark_as_read(self) -> None:
        self.read_at = datetime_utc_now()
