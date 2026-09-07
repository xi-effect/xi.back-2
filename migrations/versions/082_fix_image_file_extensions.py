"""fix_image_file_extensions

Revision ID: 082
Revises: 081
Create Date: 2026-08-31 05:33:20.524656

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "082"
down_revision: Union[str, None] = "081"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

WEBP_EXTENSION = "webp"


def upgrade() -> None:
    connection = op.get_bind()
    metadata = sa.MetaData(schema="xi_back_2")
    Files = sa.Table("files", metadata, autoload_with=connection)

    connection.execute(
        sa.update(Files)
        .where(sa.cast(Files.c.kind, sa.Text) == "IMAGE")
        .values(extension=WEBP_EXTENSION)
    )


def downgrade() -> None:
    pass  # original wrong extensions weren't recorded anywhere to restore
