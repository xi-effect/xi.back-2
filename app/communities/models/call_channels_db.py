from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.config import Base
from app.communities.models.channels_db import Channel


class CallChannel(Base):
    __tablename__ = "call_channels"

    id: Mapped[int] = mapped_column(
        ForeignKey(Channel.id, ondelete="CASCADE"),
        primary_key=True,
        autoincrement=False,
    )
    channel: Mapped[Channel] = relationship(lazy="joined")
