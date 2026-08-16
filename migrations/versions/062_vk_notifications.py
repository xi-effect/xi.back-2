"""vk_notifications

Revision ID: 062
Revises: 061
Create Date: 2026-07-19 04:38:44.688332

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from migrations.enum_migrator import EnumMigrator

# revision identifiers, used by Alembic.
revision: str = "062"
down_revision: Union[str, None] = "061"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


delivery_method_kind_enum_migrator = EnumMigrator(
    enum_name="deliverymethodkind",
    old_members=("EMAIL", "TELEGRAM"),
    new_members=("EMAIL", "TELEGRAM", "VK"),
    column_paths=[
        ("xi_back_2", "delivery_methods", "kind"),
        ("xi_back_2", "disabled_delivery_routes", "delivery_method_kind"),
    ],
)

user_contact_kind_enum_migrator = EnumMigrator(
    enum_name="contactkind",
    old_members=("PERSONAL_TELEGRAM",),
    new_members=("PERSONAL_TELEGRAM", "PERSONAL_VK"),
    column_paths=[
        ("xi_back_2", "user_contacts", "kind"),
    ],
)


def upgrade() -> None:
    bind = op.get_bind()

    op.drop_index(
        "unique_index_delivery_methods_active_or_blocked_peer_id",
        "delivery_methods",
        schema="xi_back_2",
    )
    op.drop_constraint(
        "pk_delivery_methods",
        "delivery_methods",
        type_="primary",
        schema="xi_back_2",
    )
    with delivery_method_kind_enum_migrator.upgrade(bind):
        pass
    op.create_primary_key(
        "pk_delivery_methods",
        "delivery_methods",
        ["user_id", "kind"],
        schema="xi_back_2",
    )
    op.create_index(
        "unique_index_delivery_methods_active_or_blocked_peer_id",
        "delivery_methods",
        ["kind", "peer_id"],
        unique=True,
        schema="xi_back_2",
        postgresql_where=sa.text(
            "kind IN ('TELEGRAM', 'VK') AND status IN ('ACTIVE', 'BLOCKED')"
        ),
    )

    with user_contact_kind_enum_migrator.upgrade(bind):
        pass


def downgrade() -> None:
    bind = op.get_bind()

    op.drop_index(
        "unique_index_delivery_methods_active_or_blocked_peer_id",
        "delivery_methods",
        schema="xi_back_2",
    )
    op.drop_constraint(
        "pk_delivery_methods",
        "delivery_methods",
        type_="primary",
        schema="xi_back_2",
    )
    with delivery_method_kind_enum_migrator.downgrade(bind):
        pass
    op.create_primary_key(
        "pk_delivery_methods",
        "delivery_methods",
        ["user_id", "kind"],
        schema="xi_back_2",
    )
    op.create_index(
        "unique_index_delivery_methods_active_or_blocked_peer_id",
        "delivery_methods",
        ["kind", "peer_id"],
        unique=True,
        schema="xi_back_2",
        postgresql_where=sa.text(
            "kind = 'TELEGRAM' AND status IN ('ACTIVE', 'BLOCKED')"
        ),
    )

    with user_contact_kind_enum_migrator.downgrade(bind):
        pass
