"""tasks

Revision ID: 013
Revises: 012
Create Date: 2024-09-16 21:56:22.306724

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "013"
down_revision: Union[str, None] = "012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "task_channels",
        sa.Column("id", sa.Integer(), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(
            ["id"],
            ["xi_back_2.channels.id"],
            name=op.f("fk_task_channels_id_channels"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_task_channels")),
        schema="xi_back_2",
    )
    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("kind", sa.Enum("TASK", "TEST", name="taskkind"), nullable=False),
        sa.Column("opening_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closing_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.Column("channel_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["channel_id"],
            ["xi_back_2.task_channels.id"],
            name=op.f("fk_tasks_channel_id_task_channels"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tasks")),
        schema="xi_back_2",
    )
    op.create_index(
        "hash_index_tasks_channel_id",
        "tasks",
        ["channel_id"],
        unique=False,
        schema="xi_back_2",
        postgresql_using="hash",
    )
    op.create_index(
        "hash_index_invitations_token",
        "invitations",
        ["token"],
        unique=False,
        schema="xi_back_2",
        postgresql_using="hash",
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(
        "hash_index_invitations_token",
        table_name="invitations",
        schema="xi_back_2",
        postgresql_using="hash",
    )
    op.drop_index(
        "hash_index_tasks_channel_id",
        table_name="tasks",
        schema="xi_back_2",
        postgresql_using="hash",
    )
    op.drop_table("tasks", schema="xi_back_2")
    op.drop_table("task_channels", schema="xi_back_2")
    # ### end Alembic commands ###
