from uuid import UUID, uuid4

from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import Enum
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base
from app.common.schemas.storage_sch import StorageAccessGroupKind


class AccessGroup(Base):
    __tablename__ = "access_groups"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    kind: Mapped[StorageAccessGroupKind] = mapped_column(Enum(StorageAccessGroupKind))
    related_id: Mapped[str] = mapped_column()

    InputSchema = MappedModel.create(columns=[kind, related_id])
    ResponseSchema = InputSchema.extend(columns=[id])
