from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.config import Base
from app.communities.models.channels_db import Channel


class BoardChannel(Base):
    __tablename__ = "board_channels"

    id: Mapped[int] = mapped_column(
        ForeignKey(Channel.id, ondelete="CASCADE"),
        primary_key=True,
        autoincrement=False,
    )
    channel: Mapped[Channel] = relationship(lazy="joined")

    access_group_id: Mapped[str] = mapped_column()
    ydoc_id: Mapped[str] = mapped_column()

    ResponseSchema = MappedModel.create(columns=[ydoc_id])
