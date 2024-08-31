"""better_channel_kinds

Revision ID: 007
Revises: 006
Create Date: 2024-07-22 21:23:21.633437

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

schema_name = "xi_back_2"
table_name = "channels"
column_name = "kind"
enum_name = "channeltype"

old_options = ("POSTS", "TASKS", "CHATS", "VIDEO", "BOARD")
all_options = ("POSTS", "TASKS", "CHATS", "VIDEO", "BOARD", "CHAT", "CALL")
new_options = ("POSTS", "TASKS", "BOARD", "CHAT", "CALL")

old_enum = sa.Enum(*old_options, name=enum_name)
tmp_enum = sa.Enum(*all_options, name=f"_{enum_name}")
new_enum = sa.Enum(*new_options, name=enum_name)


def upgrade() -> None:
    conn = op.get_bind()

    # create & use temp enum with new members
    tmp_enum.create(bind=conn)
    op.execute(
        f"ALTER TABLE {schema_name}.{table_name}"
        f" ALTER COLUMN {column_name}"
        f" TYPE {tmp_enum.name}"
        f" USING {column_name}::text::{tmp_enum.name}"
    )

    # drop old enum
    old_enum.drop(bind=conn)

    # update old rows
    metadata = sa.MetaData(schema=schema_name)
    Channel = sa.Table(table_name, metadata, autoload_with=conn)

    conn.execute(
        sa.update(Channel).where(Channel.c.kind == "CHATS").values(kind="CHAT")
    )
    conn.execute(
        sa.update(Channel).where(Channel.c.kind == "VIDEO").values(kind="CALL")
    )

    # remove old members by updating to the new enum
    new_enum.create(bind=conn)
    op.execute(
        f"ALTER TABLE {schema_name}.{table_name}"
        f" ALTER COLUMN {column_name}"
        f" TYPE {new_enum.name}"
        f" USING {column_name}::text::{new_enum.name}"
    )


def downgrade() -> None:
    conn = op.get_bind()

    # create & use temp enum with new members
    tmp_enum.create(bind=conn)
    op.execute(
        f"ALTER TABLE {schema_name}.{table_name}"
        f" ALTER COLUMN {column_name}"
        f" TYPE {tmp_enum.name}"
        f" USING {column_name}::text::{tmp_enum.name}"
    )

    # drop old enum
    new_enum.drop(bind=conn)

    # update old rows
    conn = op.get_bind()
    metadata = sa.MetaData(schema=schema_name)
    Channel = sa.Table("channels", metadata, autoload_with=conn)

    conn.execute(
        sa.update(Channel).where(Channel.c.kind == "CHAT").values(kind="CHATS")
    )
    conn.execute(
        sa.update(Channel).where(Channel.c.kind == "CALL").values(kind="VIDEO")
    )

    # remove old members by updating to the new enum
    old_enum.create(bind=conn)
    op.execute(
        f"ALTER TABLE {schema_name}.{table_name}"
        f" ALTER COLUMN {column_name}"
        f" TYPE {old_enum.name}"
        f" USING {column_name}::text::{old_enum.name}"
    )
