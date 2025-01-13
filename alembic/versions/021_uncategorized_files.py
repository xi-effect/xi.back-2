"""uncategorized_files

Revision ID: 021
Revises: 020
Create Date: 2025-01-02 18:27:41.379694

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "021"
down_revision: Union[str, None] = "020"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    # we don't have users yet, so it's fine to just delete data
    op.drop_table("files", schema="xi_back_2")
    sa.Enum(name="filekind").drop(bind=bind)

    new_enum = sa.Enum("UNCATEGORIZED", "IMAGE", name="filekind")
    new_enum.create(bind=bind)

    op.create_table(
        "files",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("kind", new_enum, nullable=False),
        sa.Column("creator_user_id", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_files")),
        schema="xi_back_2",
    )


def downgrade() -> None:
    bind = op.get_bind()

    op.drop_table("files", schema="xi_back_2")
    sa.Enum(name="filekind").drop(bind=bind)

    new_enum = sa.Enum("ATTACHMENT", "IMAGE", name="filekind")
    new_enum.create(bind=bind)

    op.create_table(
        "files",
        sa.Column("id", sa.UUID(), autoincrement=False, nullable=False),
        sa.Column("name", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column("kind", new_enum, autoincrement=False, nullable=False),
        sa.Column("creator_user_id", sa.INTEGER(), autoincrement=False, nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_files"),
        schema="xi_back_2",
    )
