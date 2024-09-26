from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base
from app.communities.models.channels_db import Channel


class TaskChannel(Base):
    __tablename__ = "task_channels"

    id: Mapped[int] = mapped_column(
        ForeignKey(Channel.id, ondelete="CASCADE"),
        primary_key=True,
        autoincrement=False,
    )
