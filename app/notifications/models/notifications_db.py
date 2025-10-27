from datetime import datetime
from typing import Annotated
from uuid import UUID, uuid4

from pydantic import AwareDatetime, BaseModel, Field, TypeAdapter
from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import DateTime
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

    ResponseSchema = MappedModel.create(
        columns=[
            id,
            (created_at, AwareDatetime),
            (payload, AnyNotificationPayloadSchema),
        ]
    )
