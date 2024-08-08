"""posts

Revision ID: 010
Revises: 009
Create Date: 2024-07-30 19:01:53.559068

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "posts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.Column("channel_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["channel_id"],
            ["xi_back_2.channels.id"],
            name=op.f("fk_posts_channel_id_channels"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_posts")),
        schema="xi_back_2",
    )
    op.create_index(
        "hash_index_posts_channel_id",
        "posts",
        ["channel_id"],
        unique=False,
        schema="xi_back_2",
        postgresql_using="hash",
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(
        "hash_index_posts_channel_id",
        table_name="posts",
        schema="xi_back_2",
        postgresql_using="hash",
    )
    op.drop_table(
        "posts",
        schema="xi_back_2",
    )
    # ### end Alembic commands ###
