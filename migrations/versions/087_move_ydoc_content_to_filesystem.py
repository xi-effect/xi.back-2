"""move_ydoc_content_to_filesystem

Revision ID: 087
Revises: 086
Create Date: 2026-09-11 07:34:52.094918

"""

import gzip
from pathlib import Path
from typing import Final, Sequence, Union
from uuid import UUID

import sqlalchemy as sa
from alembic import op

from app.common.config import settings

# revision identifiers, used by Alembic.
revision: str = "087"
down_revision: Union[str, None] = "086"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

YDOC_CONTENT_ROWS_PER_FETCH: Final[int] = 100


def build_ydoc_content_path(ydoc_id: UUID) -> Path:
    hex_id = ydoc_id.hex
    return settings.storage_path / "ydocs" / hex_id[:2] / hex_id[2:4] / hex_id


def upgrade() -> None:
    connection = op.get_bind()
    metadata = sa.MetaData(schema="xi_back_2")
    YDocs = sa.Table("ydocs", metadata, autoload_with=connection)

    ydoc_rows = connection.execute(
        sa.select(YDocs.c.id, YDocs.c.content)
        .where(YDocs.c.content.is_not(None), sa.func.octet_length(YDocs.c.content) > 0)
        .execution_options(yield_per=YDOC_CONTENT_ROWS_PER_FETCH)
    )
    for ydoc_row in ydoc_rows:
        content_path = build_ydoc_content_path(ydoc_row.id)
        content_path.parent.mkdir(parents=True, exist_ok=True)
        content_path.write_bytes(gzip.compress(ydoc_row.content))


def downgrade() -> None:
    connection = op.get_bind()
    metadata = sa.MetaData(schema="xi_back_2")
    YDocs = sa.Table("ydocs", metadata, autoload_with=connection)

    connection.execute(
        sa.update(YDocs).where(YDocs.c.content.is_not(None)).values(content=None)
    )
    for ydoc_id in connection.execute(sa.select(YDocs.c.id)).scalars().all():
        content_path = build_ydoc_content_path(ydoc_id)
        if not content_path.is_file():
            continue
        connection.execute(
            sa.update(YDocs)
            .where(YDocs.c.id == ydoc_id)
            .values(content=gzip.decompress(content_path.read_bytes()))
        )
        content_path.unlink()
