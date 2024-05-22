from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base
from app.communities.models.communities_db import Community


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    community_id: Mapped[int] = mapped_column(
        ForeignKey(Community.id, ondelete="CASCADE")
    )

    __table_args__ = (
        Index("(hash_index_roles_community_id", community_id, postgresql_using="hash"),
    )

    FullInputSchema = MappedModel.create(columns=[name])
    FullPatchSchema = FullInputSchema.as_patch()
    FullResponseSchema = FullInputSchema.extend(columns=[id])
