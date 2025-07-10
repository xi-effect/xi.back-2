"""personal_access_group

Revision ID: 032
Revises: 031
Create Date: 2025-07-11 15:13:28.297185

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "032"
down_revision: Union[str, None] = "031"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

schema_name = "xi_back_2"
table_name = "access_groups"
column_name = "kind"
enum_name = "storageaccessgroupkind"


old_options = ("BOARD_CHANNEL",)
all_options = ("BOARD_CHANNEL", "PERSONAL")
new_options = ("BOARD_CHANNEL", "PERSONAL")

old_enum = sa.Enum(*old_options, name=enum_name)
tmp_enum = sa.Enum(*all_options, name=f"_{enum_name}")
new_enum = sa.Enum(*new_options, name=enum_name)


def upgrade() -> None:
    op.execute(f"ALTER TYPE {enum_name} ADD VALUE 'PERSONAL'")


def downgrade() -> None:
    conn = op.get_bind()

    # create & use temp enum with new members
    tmp_enum.create(bind=conn)
    op.execute(
        f"ALTER TABLE {schema_name}.{table_name}"
        f" ALTER COLUMN {column_name}"
        f" TYPE {tmp_enum.name}"
        f" USING {column_name}::text::{tmp_enum.name}"
    )

    # drop old enum
    new_enum.drop(bind=conn)

    # remove old members by updating to the new enum
    old_enum.create(bind=conn)
    op.execute(
        f"ALTER TABLE {schema_name}.{table_name}"
        f" ALTER COLUMN {column_name}"
        f" TYPE {old_enum.name}"
        f" USING {column_name}::text::{old_enum.name}"
    )

    # remove temp enum
    op.execute(f"DROP TYPE {tmp_enum.name}")
