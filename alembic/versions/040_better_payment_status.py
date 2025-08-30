"""better_payment_status

Revision ID: 040
Revises: 039
Create Date: 2025-09-05 00:26:49.724648

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "040"
down_revision: Union[str, None] = "039"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

schema_name = "xi_back_2"
table_name = "recipient_invoices"
column_name = "status"
enum_name = "paymentstatus"

old_options = ("WF_PAYMENT", "WF_CONFIRMATION", "CANCELED", "COMPLETE")
all_options = (
    "WF_PAYMENT",
    "WF_CONFIRMATION",
    "CANCELED",
    "COMPLETE",
    "WF_SENDER_CONFIRMATION",
    "WF_RECEIVER_CONFIRMATION",
)
new_options = ("WF_SENDER_CONFIRMATION", "WF_RECEIVER_CONFIRMATION", "COMPLETE")

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
    RecipientInvoice = sa.Table(table_name, metadata, autoload_with=conn)

    conn.execute(
        sa.update(RecipientInvoice)
        .where(RecipientInvoice.c.status == "WF_PAYMENT")
        .values(status="WF_SENDER_CONFIRMATION")
    )
    conn.execute(
        sa.update(RecipientInvoice)
        .where(RecipientInvoice.c.status == "WF_CONFIRMATION")
        .values(status="WF_RECEIVER_CONFIRMATION")
    )

    # remove old members by updating to the new enum
    new_enum.create(bind=conn)
    op.execute(
        f"ALTER TABLE {schema_name}.{table_name}"
        f" ALTER COLUMN {column_name}"
        f" TYPE {new_enum.name}"
        f" USING {column_name}::text::{new_enum.name}"
    )

    # remove tmp enum
    tmp_enum.drop(bind=conn)


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
    metadata = sa.MetaData(schema=schema_name)
    RecipientInvoice = sa.Table(table_name, metadata, autoload_with=conn)

    conn.execute(
        sa.update(RecipientInvoice)
        .where(RecipientInvoice.c.status == "WF_SENDER_CONFIRMATION")
        .values(status="WF_PAYMENT")
    )
    conn.execute(
        sa.update(RecipientInvoice)
        .where(RecipientInvoice.c.status == "WF_RECEIVER_CONFIRMATION")
        .values(status="WF_CONFIRMATION")
    )

    # remove old members by updating to the new enum
    old_enum.create(bind=conn)
    op.execute(
        f"ALTER TABLE {schema_name}.{table_name}"
        f" ALTER COLUMN {column_name}"
        f" TYPE {old_enum.name}"
        f" USING {column_name}::text::{old_enum.name}"
    )

    # remove tmp enum
    tmp_enum.drop(bind=conn)
