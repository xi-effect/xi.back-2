from uuid import UUID, uuid4

from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import ForeignKey, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.config import Base
from app.storage.models.access_groups_db import AccessGroup


class YDoc(Base):
    __tablename__ = "ydocs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    access_group_id: Mapped[UUID] = mapped_column(
        ForeignKey(AccessGroup.id, ondelete="CASCADE")
    )
    access_group: Mapped[AccessGroup] = relationship(passive_deletes=True)

    content: Mapped[bytes | None] = mapped_column(LargeBinary)

    ResponseSchema = MappedModel.create(columns=[id])
