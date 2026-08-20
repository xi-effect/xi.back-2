"""deprecate_materials

Revision ID: 073
Revises: 072
Create Date: 2026-08-21 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "073"
down_revision: Union[str, None] = "072"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.rename_table(
        "materials",
        "materials_old",
        schema="xi_back_2",
    )

    op.drop_constraint(
        "pk_materials",
        "materials_old",
        schema="xi_back_2",
    )
    op.create_primary_key(
        "pk_materials_old",
        "materials_old",
        ["id"],
        schema="xi_back_2",
    )


def downgrade() -> None:
    op.drop_constraint(
        "pk_materials_old",
        "materials_old",
        schema="xi_back_2",
    )
    op.create_primary_key(
        "pk_materials",
        "materials_old",
        ["id"],
        schema="xi_back_2",
    )

    op.rename_table(
        "materials_old",
        "materials",
        schema="xi_back_2",
    )
