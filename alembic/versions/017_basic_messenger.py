"""basic-messenger

Revision ID: 017
Revises: 016
Create Date: 2024-11-09 20:54:38.619763

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "017"
down_revision: Union[str, None] = "016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

schema_name = "xi_back_2"
table_name = "access_groups"
column_name = "kind"

old_enum = sa.Enum("BOARD_CHANNEL", name="accessgroupkind")
new_enum = sa.Enum("BOARD_CHANNEL", name="storageaccessgroupkind")


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "chats",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "access_kind",
            sa.Enum("CHAT_CHANNEL", name="chataccesskind"),
            nullable=False,
        ),
        sa.Column("related_id", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_chats")),
        schema="xi_back_2",
    )
    op.create_table(
        "messages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sender_user_id", sa.Integer(), nullable=False),
        sa.Column("chat_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["chat_id"],
            ["xi_back_2.chats.id"],
            name=op.f("fk_messages_chat_id_chats"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_messages")),
        schema="xi_back_2",
    )
    op.create_index(
        op.f("ix_xi_back_2_messages_chat_id"),
        "messages",
        ["chat_id"],
        unique=False,
        schema="xi_back_2",
    )
    op.create_index(
        op.f("ix_xi_back_2_messages_created_at"),
        "messages",
        ["created_at"],
        unique=False,
        schema="xi_back_2",
    )
    op.create_table(
        "chat_channels",
        sa.Column("id", sa.Integer(), autoincrement=False, nullable=False),
        sa.Column("chat_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["id"],
            ["xi_back_2.channels.id"],
            name=op.f("fk_chat_channels_id_channels"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_chat_channels")),
        schema="xi_back_2",
    )

    conn = op.get_bind()
    new_enum.create(bind=conn)
    op.execute(
        f"ALTER TABLE {schema_name}.{table_name}"
        f" ALTER COLUMN {column_name}"
        f" TYPE {new_enum.name}"
        f" USING {column_name}::text::{new_enum.name}"
    )
    old_enum.drop(bind=conn)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    conn = op.get_bind()
    old_enum.create(bind=conn)
    op.execute(
        f"ALTER TABLE {schema_name}.{table_name}"
        f" ALTER COLUMN {column_name}"
        f" TYPE {old_enum.name}"
        f" USING {column_name}::text::{old_enum.name}"
    )
    new_enum.drop(bind=conn)

    op.drop_table("chat_channels", schema="xi_back_2")
    op.drop_index(
        op.f("ix_xi_back_2_messages_created_at"),
        table_name="messages",
        schema="xi_back_2",
    )
    op.drop_index(
        op.f("ix_xi_back_2_messages_chat_id"), table_name="messages", schema="xi_back_2"
    )
    op.drop_table("messages", schema="xi_back_2")
    op.drop_table("chats", schema="xi_back_2")
    # ### end Alembic commands ###
