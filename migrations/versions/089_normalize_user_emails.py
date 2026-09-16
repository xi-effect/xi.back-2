"""normalize_user_emails

Revision ID: 089
Revises: 088
Create Date: 2026-09-16 04:39:43.435530

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "089"
down_revision: Union[str, None] = "088"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    connection = op.get_bind()
    metadata = sa.MetaData(schema="xi_back_2")
    Users = sa.Table("users", metadata, autoload_with=connection)
    DeliveryMethods = sa.Table("delivery_methods", metadata, autoload_with=connection)

    normalized_email = sa.func.lower(sa.func.trim(Users.c.email))

    collision_count = connection.execute(
        sa.select(sa.func.count()).select_from(
            sa.select(normalized_email)
            .group_by(normalized_email)
            .having(sa.func.count() > 1)
            .subquery()
        )
    ).scalar_one()
    if collision_count != 0:
        raise RuntimeError(
            f"{collision_count} emails belong to several users after normalization"
        )

    connection.execute(sa.update(Users).values(email=normalized_email))
    connection.execute(
        sa.update(DeliveryMethods)
        .where(DeliveryMethods.c.user_id == Users.c.id)
        .where(sa.cast(DeliveryMethods.c.kind, sa.Text) == "EMAIL")
        .values(email=Users.c.email)
    )


def downgrade() -> None:
    pass  # original spellings weren't recorded anywhere to restore
