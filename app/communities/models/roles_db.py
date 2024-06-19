import enum
from typing import Annotated

from pydantic import Field
from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import Enum, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.config import Base
from app.communities.models.communities_db import Community


class Permission(str, enum.Enum):
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
        passive_deletes=True, cascade="all, delete-orphan", lazy="selectin"
    )

    @property
    def permission_list(self) -> list[Permission]:  # noqa
        return [permission.permission for permission in self.permissions]

    __table_args__ = (
        Index("hash_index_roles_community_id", community_id, postgresql_using="hash"),
    )

    NameType = Annotated[str, Field(min_length=1, max_length=32)]
    ColorType = Annotated[str, Field(min_length=6, max_length=6)]

    InputSchema = MappedModel.create(columns=[(name, NameType), (color, ColorType)])
    PatchSchema = InputSchema.as_patch()
    ResponseSchema = InputSchema.extend(columns=[id])
    ListPermissionsSchema = ResponseSchema.extend(properties=[permission_list])


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
