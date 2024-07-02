"""board_channel_type

Revision ID: 006
Revises: 005
Create Date: 2024-06-01 19:50:05.491293

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    enum_name: str = "channeltype"
    new_value: str = "BOARD"
    op.execute(f"ALTER TYPE {enum_name} ADD VALUE '{new_value}'")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass  # lazy
    # ### end Alembic commands ###