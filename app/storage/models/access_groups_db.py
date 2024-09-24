from uuid import UUID, uuid4

from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import Enum
from sqlalchemy.orm import Mapped, mapped_column

from app.common.access import AccessGroupKind
from app.common.config import Base


class AccessGroup(Base):
    __tablename__ = "access_groups"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    kind: Mapped[AccessGroupKind] = mapped_column(Enum(AccessGroupKind))
    related_id: Mapped[str] = mapped_column()

    InputSchema = MappedModel.create(columns=[kind, related_id])
    ResponseSchema = InputSchema.extend(columns=[id])
