"""new_onboarding

Revision ID: 031
Revises: 030
Create Date: 2025-06-29 19:00:30.649375

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "031"
down_revision: Union[str, None] = "030"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


new_enum = sa.Enum(
    "USER_INFORMATION",
    "DEFAULT_LAYOUT",
    "NOTIFICATIONS",
    "TRAINING",
    "COMPLETED",
    name="onboarding_stage_2",
)
old_enum = sa.Enum(
    "CREATED",
    "COMMUNITY_CHOICE",
    "COMMUNITY_CREATE",
    "COMMUNITY_INVITE",
    "COMPLETED",
    name="onboarding_stage",
)


def upgrade() -> None:
    # Written manually to clear old onboarding data
    bind = op.get_bind()

    op.drop_column(
        table_name="users",
        column_name="onboarding_stage",
        schema="xi_back_2",
    )
    old_enum.drop(op.get_bind())

    new_enum.create(bind=bind)
    op.add_column(
        table_name="users",
        column=sa.Column(
            "onboarding_stage",
            new_enum,
            nullable=False,
            server_default="USER_INFORMATION",
        ),
        schema="xi_back_2",
    )


def downgrade() -> None:
    # Written manually to clear new onboarding data
    bind = op.get_bind()

    op.drop_column(
        table_name="users",
        column_name="onboarding_stage",
        schema="xi_back_2",
    )
    new_enum.drop(op.get_bind())

    old_enum.create(bind=bind)
    op.add_column(
        table_name="users",
        column=sa.Column(
            "onboarding_stage",
            old_enum,
            nullable=False,
            server_default="CREATED",
        ),
        schema="xi_back_2",
    )
