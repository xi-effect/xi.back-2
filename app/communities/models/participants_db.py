from collections.abc import Sequence
from datetime import datetime
from typing import Self

from pydantic import NaiveDatetime
from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import ForeignKey, Index, Row, select
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.config import DB_SCHEMA, Base
from app.common.sqlalchemy_ext import db
from app.communities.models.communities_db import Community
from app.communities.models.roles_db import Role


class Participant(Base):
    __tablename__ = "participants"

    # participant data
    id: Mapped[int] = mapped_column(primary_key=True)
    is_owner: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    # TODO mb change to `DateTime(timezone=True)`

    # user data
    user_id: Mapped[int] = mapped_column()

    # community data
    community_id: Mapped[int] = mapped_column(
        ForeignKey(Community.id, ondelete="CASCADE")
    )
    community: Mapped[Community] = relationship(passive_deletes=True)

    # role data
    roles: Mapped[list[Role]] = relationship(
        passive_deletes=True,
        secondary=(
            "participant_roles"
            if DB_SCHEMA is None
            else f"{DB_SCHEMA}.participant_roles"
        ),
        lazy="selectin",
    )

    @property
    def participant_roles(self) -> list[Role.ResponseSchema]:
        return [Role.ResponseSchema.from_orm(role) for role in self.roles]

    # indexes
    __table_args__ = (
        Index("hash_index_user_id", user_id, postgresql_using="hash"),
        Index("hash_index_community_id", community_id, postgresql_using="hash"),
    )

    # models
    CurrentSchema = MappedModel.create(columns=[is_owner])
    IDsSchema = MappedModel.create(columns=[community_id, user_id])
    MUBBaseSchema = CurrentSchema.extend(columns=[(created_at, NaiveDatetime)])
    MUBPatchSchema = MUBBaseSchema.as_patch()
    MUBItemSchema = MUBBaseSchema.extend(columns=[id, user_id])
    MUBResponseSchema = MUBItemSchema.extend(properties=[participant_roles])
    ListItemSchema = MUBBaseSchema.extend(columns=[user_id])
    ServerEventSchema = ListItemSchema.extend(columns=[community_id])

    # participant repository
    @classmethod
    async def find_all_by_community_id(cls, community_id: int) -> Sequence[Self]:
        # TODO pagination and search
        return await cls.find_all_by_kwargs(  # TODO (37570606) pragma: no cover
            cls.created_at.desc(), community_id=community_id
        )

    # community-2-participant repository
    @classmethod
    async def find_first_community_by_user_id(
        cls, user_id: int
    ) -> Row[tuple[Community, Self]] | None:
        return await db.get_first_row(
            select(Community, cls).join(cls).filter(cls.user_id == user_id).limit(1)
        )

    @classmethod
    async def find_all_communities_by_user_id(cls, user_id: int) -> Sequence[Community]:
        return await db.get_all(
            select(Community).join(cls).filter(cls.user_id == user_id)
        )


class ParticipantRole(Base):
    __tablename__ = "participant_roles"

    participant_id: Mapped[int] = mapped_column(
        ForeignKey(Participant.id, ondelete="CASCADE"), primary_key=True
    )
    role_id: Mapped[int] = mapped_column(
        ForeignKey(Role.id, ondelete="CASCADE"), primary_key=True
    )
