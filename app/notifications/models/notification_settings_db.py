from typing import Literal

from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base


class NotificationSettings(Base):
    __tablename__ = "notification_settings"

    user_id: Mapped[int] = mapped_column(primary_key=True)

    event_reminder_offset_minutes: Mapped[int] = mapped_column(default=30)

    EventReminderOffsetMinutesType = Literal[5, 15, 30, 60]

    InputSchema = MappedModel.create(
        columns=[(event_reminder_offset_minutes, EventReminderOffsetMinutesType)]
    )
    PatchSchema = InputSchema.as_patch()
    ResponseSchema = InputSchema.extend()
