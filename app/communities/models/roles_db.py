from collections.abc import Sequence
from enum import StrEnum
from typing import Annotated, Self

from pydantic import Field
from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import Enum, ForeignKey, Index, String, select
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.config import Base
from app.common.sqlalchemy_ext import db
from app.communities.models.communities_db import Community


class Permission(StrEnum):
    VIEW_CHANNELS = "view-channels"
    VIEW_ACTIVITY = "view-activity"
    MANAGE_ROLES = "manage-roles"
    MANAGE_INVITATIONS = "manage-invitations"
    MANAGE_PARTICIPANTS = "manage-participants"
    MANAGE_CHANNELS = "manage-channels"


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(32))
    color: Mapped[str] = mapped_column(String(6))

    community_id: Mapped[int] = mapped_column(
        ForeignKey(Community.id, ondelete="CASCADE")
    )
    community: Mapped[Community] = relationship(passive_deletes=True)

    permissions: Mapped[list["RolePermission"]] = relationship(
        cascade="all, delete-orphan", lazy="selectin"
    )

    @property
    def role_permissions(self) -> list[Permission]:
        return [permission.permission for permission in self.permissions]

    __table_args__ = (
        Index("hash_index_roles_community_id", community_id, postgresql_using="hash"),
    )

    NameType = Annotated[str, Field(min_length=1, max_length=32)]
    ColorType = Annotated[str, Field(min_length=6, max_length=6)]

    InputSchema = MappedModel.create(columns=[(name, NameType), (color, ColorType)])
    PatchSchema = InputSchema.as_patch()
    ItemSchema = InputSchema.extend(columns=[id])
    ResponseSchema = ItemSchema.extend(properties=[role_permissions])

    @classmethod
    async def find_paginated_by_community_id(
        cls,
        community_id: int,
        offset: int,
        limit: int,
    ) -> Sequence[Self]:
        stmt = select(cls).filter_by(community_id=community_id)
        return await db.get_paginated(stmt, offset, limit)


class RolePermission(Base):
    __tablename__ = "role_permissions"

    role_id: Mapped[int] = mapped_column(
        ForeignKey(Role.id, ondelete="CASCADE"),
        primary_key=True,
    )
    permission: Mapped[Permission] = mapped_column(Enum(Permission), primary_key=True)

    __table_args__ = (
        Index("hash_index_role_permissions_role_id", role_id, postgresql_using="hash"),
    )

    @classmethod
    async def modify_role_permissions(
        cls,
        role_id: int,
        current_permissions: list[Permission],
        patch_permissions: list[Permission],
    ) -> Sequence[Self]:
        for patch_permission in patch_permissions:
            if patch_permission not in current_permissions:
                await cls.create(role_id=role_id, permission=patch_permission)

        for current_permission in current_permissions:
            if current_permission not in patch_permissions:
                role_permission = await cls.find_first_by_kwargs(
                    role_id=role_id, permission=current_permission
                )
                if role_permission:
                    await role_permission.delete()

        return await cls.find_all_by_kwargs(role_id=role_id)
