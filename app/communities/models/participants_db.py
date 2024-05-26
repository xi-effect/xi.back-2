from datetime import datetime

from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.config import Base
from app.communities.models.communities_db import Community
from app.communities.models.roles_db import Role


class Participant(Base):
    __tablename__ = "participants"

    # participant data
    id: Mapped[int] = mapped_column(primary_key=True)
    is_owner: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    # user data
    user_id: Mapped[int] = mapped_column()

    # community data
    community_id: Mapped[int] = mapped_column(
        ForeignKey(Community.id, ondelete="CASCADE")
    )
    community: Mapped[Community] = relationship(passive_deletes=True)

    # role data
    roles: Mapped[list[Role]] = relationship(
        passive_deletes=True, secondary="participant_roles", lazy="selectin"
    )

    # indexes
    __table_args__ = (
        Index("hash_index_user_id", user_id, postgresql_using="hash"),
        Index("hash_index_community_id", community_id, postgresql_using="hash"),
    )

    # models
    MUBBaseSchema = MappedModel.create(columns=[is_owner, created_at])
    MUBPatchSchema = MUBBaseSchema.as_patch()
    FullResponseSchema = MUBBaseSchema.extend(columns=[id, user_id])


class ParticipantRole(Base):
    __tablename__ = "participant_roles"

    participant_id: Mapped[int] = mapped_column(
        ForeignKey(Participant.id, ondelete="CASCADE"), primary_key=True
    )
    role_id: Mapped[int] = mapped_column(
        ForeignKey(Role.id, ondelete="CASCADE"), primary_key=True
    )
