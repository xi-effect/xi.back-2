import enum

from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import Enum, ForeignKey, Index, String, delete
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.config import Base
from app.common.sqlalchemy_ext import db
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
    color: Mapped[str | None] = mapped_column(String(6))
    community_id: Mapped[int] = mapped_column(
        ForeignKey(Community.id, ondelete="CASCADE")
    )

    community: Mapped[Community] = relationship(passive_deletes=True)

    permissions_r: Mapped[list["RolePermission"]] = relationship(
        passive_deletes=True, lazy="joined"
    )

    @property
    def permissions(self) -> list[str]:
        return [permission.permission for permission in self.permissions_r]

    __table_args__ = (
        Index("hash_index_roles_community_id", community_id, postgresql_using="hash"),
    )

    InputSchema = MappedModel.create(columns=[name, color])
    ResponseSchema = InputSchema.extend(columns=[id])
    PatchSchema = InputSchema.as_patch()
    PermissionsResponseSchema = ResponseSchema.extend(properties=[permissions])


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
    async def create_bulk(cls, role_id: int, permissions: list[Permission]) -> None:
        db.session.add_all(
            cls(role_id=role_id, permission=permission) for permission in permissions
        )
        await db.session.flush()

    @classmethod
    async def delete_all_by_id(cls, role_id: int) -> None:
        await db.session.execute(delete(cls).where(cls.role_id == role_id))
