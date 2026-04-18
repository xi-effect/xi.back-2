"""audio_files

Revision ID: 069
Revises: 068
Create Date: 2026-04-17 04:07:30.284265

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

schema_name = "xi_back_2"
table_name = "files"
column_name = "kind"
enum_name = "file_kind"
tmp_enum_name = f"_{enum_name}"

old_enum = sa.Enum("UNCATEGORIZED", "IMAGE", "DOCUMENT", name=enum_name)

# revision identifiers, used by Alembic.
revision: str = "069"
down_revision: Union[str, None] = "068"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(f"ALTER TYPE {enum_name} ADD VALUE 'AUDIO'")


def downgrade() -> None:
    conn = op.get_bind()

    # rename new enum
    op.execute(f"ALTER TYPE {enum_name} RENAME TO {tmp_enum_name}")

    # update old rows
    metadata = sa.MetaData(schema=schema_name)
    Files = sa.Table(table_name, metadata, autoload_with=conn)

    conn.execute(
        sa.update(Files).where(Files.c.kind == "AUDIO").values(kind="UNCATEGORIZED")
    )

    # remove old members by updating to the new enum
    old_enum.create(bind=conn)
    op.execute(
        f"ALTER TABLE {schema_name}.{table_name}"
        f" ALTER COLUMN {column_name}"
        f" TYPE {old_enum.name}"
        f" USING {column_name}::text::{old_enum.name}"
    )

    # remove new enum
    op.execute(f"DROP TYPE {tmp_enum_name}")
