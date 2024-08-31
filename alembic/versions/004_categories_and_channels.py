"""categories_and_channels

Revision ID: 004
Revises: 003
Create Date: 2024-05-15 20:42:05.528503

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "categories",
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("community_id", sa.Integer(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["community_id"],
            ["xi_back_2.communities.id"],
            name=op.f("fk_categories_community_id_communities"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_categories")),
        schema="xi_back_2",
    )
    op.create_index(
        "hash_index_categories_community_id",
        "categories",
        ["community_id"],
        unique=False,
        schema="xi_back_2",
        postgresql_using="hash",
    )

    op.create_table(
        "channels",
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "kind",
            sa.Enum("POSTS", "TASKS", "CHATS", "VIDEO", name="channeltype"),
            nullable=False,
        ),
        sa.Column("community_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["xi_back_2.categories.id"],
            name=op.f("fk_channels_category_id_categories"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["community_id"],
            ["xi_back_2.communities.id"],
            name=op.f("fk_channels_community_id_communities"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_channels")),
        schema="xi_back_2",
    )
    op.create_index(
        "hash_index_channels_category_id",
        "channels",
        ["category_id"],
        unique=False,
        schema="xi_back_2",
        postgresql_using="hash",
    )
    op.create_index(
        "hash_index_channels_community_id",
        "channels",
        ["community_id"],
        unique=False,
        schema="xi_back_2",
        postgresql_using="hash",
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(
        "hash_index_channels_community_id",
        table_name="channels",
        schema="xi_back_2",
        postgresql_using="hash",
    )
    op.drop_index(
        "hash_index_channels_category_id",
        table_name="channels",
        schema="xi_back_2",
        postgresql_using="hash",
    )
    op.drop_table("channels", schema="xi_back_2")
    op.drop_index(
        "hash_index_categories_community_id",
        table_name="categories",
        schema="xi_back_2",
        postgresql_using="hash",
    )
    op.drop_table("categories", schema="xi_back_2")
    # ### end Alembic commands ###
