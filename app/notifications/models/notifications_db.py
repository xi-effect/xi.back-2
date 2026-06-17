from datetime import datetime
from typing import Annotated
from uuid import UUID, uuid4

from pydantic import AwareDatetime, BaseModel, Field, TypeAdapter
from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base
from app.common.schemas.notifications_sch import AnyNotificationPayloadSchema
from app.common.sqlalchemy_ext import PydanticJSONType
from app.common.utils.datetime import datetime_utc_now


class NotificationCursorSchema(BaseModel):
    created_at: AwareDatetime


class NotificationSearchRequestSchema(BaseModel):
    cursor: NotificationCursorSchema | None = None
    limit: Annotated[int, Field(gt=0, lt=100)] = 12


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime_utc_now,
        index=True,
    )

    payload: Mapped[AnyNotificationPayloadSchema] = mapped_column(
        PydanticJSONType(TypeAdapter(AnyNotificationPayloadSchema))
    )

    idempotency_key: Mapped[str | None] = mapped_column(String(100))
    idempotency_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=None,
    )

    __table_args__ = (
        Index(
            "unique_index_notifications_idempotency",
            idempotency_key,
            unique=True,
            postgresql_where=idempotency_key.is_not(None),
        ),
    )

    ResponseSchema = MappedModel.create(
        columns=[
            id,
            (created_at, AwareDatetime),
            (payload, AnyNotificationPayloadSchema),
        ]
    )

    @classmethod
    async def is_idempotency_violated(
        cls, idempotency_key: str | None
    ) -> bool:  # pragma: no cover
        if idempotency_key is None:
            return False

        result = await cls.find_first_by_kwargs(idempotency_key=idempotency_key)
        if result is None:
            return False

        if (
            result.idempotency_expires_at is not None
            and result.idempotency_expires_at < datetime_utc_now()
        ):
            result.idempotency_key = None
            result.idempotency_expires_at = None
            return False

        return True
