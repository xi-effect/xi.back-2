from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base


class EmailConnection(Base):
    __tablename__ = "email_connections"

    user_id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(100), index=True)

    InputSchema = MappedModel.create(columns=[email])
