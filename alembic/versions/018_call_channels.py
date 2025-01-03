"""call_channels

Revision ID: 018
Revises: 017
Create Date: 2024-11-24 23:16:36.063932

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "018"
down_revision: Union[str, None] = "017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "call_channels",
        sa.Column("id", sa.Integer(), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(
            ["id"],
            ["xi_back_2.channels.id"],
            name=op.f("fk_call_channels_id_channels"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_call_channels")),
        schema="xi_back_2",
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("call_channels", schema="xi_back_2")
    # ### end Alembic commands ###
