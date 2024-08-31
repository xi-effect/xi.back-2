from sqlalchemy import ForeignKey, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base
from app.communities.models.channels_db import Channel


class BoardChannel(Base):
    __tablename__ = "board_channels"

    id: Mapped[int] = mapped_column(
        ForeignKey(Channel.id, ondelete="CASCADE"),
        primary_key=True,
        autoincrement=False,
    )
    content: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
