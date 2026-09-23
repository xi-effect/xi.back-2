"""rename_plan_kind_enum

Revision ID: 094
Revises: 093
Create Date: 2026-09-23 04:40:35.049810

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "094"
down_revision: Union[str, None] = "093"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE subscriptionplankind RENAME TO paidplankind")


def downgrade() -> None:
    op.execute("ALTER TYPE paidplankind RENAME TO subscriptionplankind")
