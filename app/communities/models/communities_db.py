from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base


class Community(Base):
    __tablename__ = "communities"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)

    FullInputSchema = MappedModel.create(columns=[name, description])
    FullPatchSchema = FullInputSchema.as_patch()
    FullResponseSchema = FullInputSchema.extend(columns=[id])
