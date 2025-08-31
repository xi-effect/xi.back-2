"""invoices_payment_type

Revision ID: 037
Revises: 036
Create Date: 2025-08-13 02:33:37.246188

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "037"
down_revision: Union[str, None] = "036"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


new_enum = sa.Enum("TRANSFER", "CASH", name="paymenttype")


def upgrade() -> None:
    conn = op.get_bind()
    new_enum.create(bind=conn)

    op.add_column(
        "recipient_invoices",
        sa.Column(
            "payment_type",
            new_enum,
            nullable=True,
        ),
        schema="xi_back_2",
    )


def downgrade() -> None:
    conn = op.get_bind()
    op.drop_column("recipient_invoices", "payment_type", schema="xi_back_2")
    new_enum.drop(bind=conn)
