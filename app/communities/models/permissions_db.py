import enum

from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import Enum, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base
from app.communities.models.roles_db import Role


class Permission(str, enum.Enum):
    VIEW_CHANNELS = "view-channels"
    VIEW_ACTIVITY = "view-activity"
    MANAGE_ROLES = "manage-roles"
    MANAGE_INVITATIONS = "manage-invitations"
    MANAGE_PARTICIPANTS = "manage-participants"
    MANAGE_CHANNELS = "manage-channels"


class RolePermission(Base):
    __tablename__ = "role_permissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey(Role.id, ondelete="CASCADE"))
    permission: Mapped[Permission] = mapped_column(Enum(Permission))

    __table_args__ = (
        Index("hash_index_role_permissions_role_id", role_id, postgresql_using="hash"),
    )

    FullResponseSchema = MappedModel.create(columns=[id, permission])
