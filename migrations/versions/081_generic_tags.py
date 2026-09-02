"""generic_tags

Revision ID: 081
Revises: 080
Create Date: 2026-08-30 17:13:46.518226

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from migrations.enum_migrator import EnumMigrator

# revision identifiers, used by Alembic.
revision: str = "081"
down_revision: Union[str, None] = "080"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


tag_kind_enum_migrator = EnumMigrator(
    enum_name="tagkind",
    old_members=("SUBJECT",),
    new_members=("SUBJECT", "GENERIC"),
    column_paths=[
        ("xi_back_2", "tags", "kind"),
    ],
)


def upgrade() -> None:
    with tag_kind_enum_migrator.upgrade(op.get_bind()):
        pass


def downgrade() -> None:
    bind = op.get_bind()

    metadata = sa.MetaData(schema="xi_back_2")
    Tag = sa.Table("tags", metadata, autoload_with=bind)
    bind.execute(
        sa.delete(Tag).where(Tag.c.kind == sa.literal_column("'GENERIC'::tagkind"))
    )

    with tag_kind_enum_migrator.downgrade(bind):
        pass
