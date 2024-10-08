"""move-ydocs-to-storage

Revision ID: 016
Revises: 015
Create Date: 2024-09-14 20:19:54.502385

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "016"
down_revision: Union[str, None] = "015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # we don't have users yet, so it's fine to just delete data
    op.execute("TRUNCATE TABLE xi_back_2.board_channels")

    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "board_channels",
        sa.Column("access_group_id", sa.String(), nullable=False),
        schema="xi_back_2",
    )
    op.add_column(
        "board_channels",
        sa.Column("ydoc_id", sa.String(), nullable=False),
        schema="xi_back_2",
    )
    op.drop_column("board_channels", "content", schema="xi_back_2")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "board_channels",
        sa.Column("content", sa.LargeBinary(), autoincrement=False, nullable=True),
        schema="xi_back_2",
    )
    op.drop_column("board_channels", "ydoc_id", schema="xi_back_2")
    op.drop_column("board_channels", "access_group_id", schema="xi_back_2")
    # ### end Alembic commands ###
