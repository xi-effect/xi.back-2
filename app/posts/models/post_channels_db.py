from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base


class PostChannel(Base):
    __tablename__ = "post_channels"

    id: Mapped[int] = mapped_column(primary_key=True)
    community_id: Mapped[int] = mapped_column()

    InputSchema = MappedModel.create(columns=[community_id])
