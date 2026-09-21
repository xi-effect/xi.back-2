from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, select
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base
from app.common.sqlalchemy_ext import db
from app.common.utils.datetime import datetime_utc_now
from app.subscriptions.models.promocodes_db import Promocode


class PromocodeRedemption(Base):
    __tablename__ = "promocode_redemptions"

    promocode_id: Mapped[int] = mapped_column(
        ForeignKey(Promocode.id, ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime_utc_now
    )

    @classmethod
    async def is_present_by_ids(cls, promocode_id: int, user_id: int) -> bool:
        return await db.is_present(
            select(cls).filter_by(promocode_id=promocode_id, user_id=user_id)
        )
