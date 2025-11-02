from uuid import UUID, uuid4

from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import LargeBinary
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base


class YDoc(Base):
    __tablename__ = "ydocs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    content: Mapped[bytes | None] = mapped_column(LargeBinary, default=None)

    ResponseSchema = MappedModel.create(columns=[id])
