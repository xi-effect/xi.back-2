"""deprecate_storage_v1

Revision ID: 045
Revises: 044
Create Date: 2025-10-25 20:01:58.688339

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "045"
down_revision: Union[str, None] = "044"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.rename_table(
        "access_groups",
        "access_groups_old",
        schema="xi_back_2",
    )
    op.rename_table(
        "files",
        "files_old",
        schema="xi_back_2",
    )
    op.rename_table(
        "ydocs",
        "ydocs_old",
        schema="xi_back_2",
    )

    op.drop_constraint(
        "fk_ydocs_access_group_id_access_groups",
        table_name="ydocs_old",
        schema="xi_back_2",
    )
    op.drop_constraint(
        "fk_files_access_group_id_access_groups",
        table_name="files_old",
        schema="xi_back_2",
    )
    op.drop_constraint(
        "pk_access_groups",
        "access_groups_old",
        schema="xi_back_2",
    )
    op.drop_constraint(
        "pk_ydocs",
        "ydocs_old",
        schema="xi_back_2",
    )
    op.drop_constraint(
        "pk_files",
        "files_old",
        schema="xi_back_2",
    )

    op.create_primary_key(
        "pk_files_old",
        "files_old",
        ["id"],
        schema="xi_back_2",
    )
    op.create_primary_key(
        "pk_ydocs_old",
        "ydocs_old",
        ["id"],
        schema="xi_back_2",
    )
    op.create_primary_key(
        "pk_access_groups_old",
        "access_groups_old",
        ["id"],
        schema="xi_back_2",
    )
    op.create_foreign_key(
        "fk_files_old_access_group_id_access_groups_old",
        source_table="files_old",
        referent_table="access_groups_old",
        local_cols=["access_group_id"],
        remote_cols=["id"],
        source_schema="xi_back_2",
        referent_schema="xi_back_2",
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_ydocs_old_access_group_id_access_groups_old",
        source_table="ydocs_old",
        referent_table="access_groups_old",
        local_cols=["access_group_id"],
        remote_cols=["id"],
        source_schema="xi_back_2",
        referent_schema="xi_back_2",
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.rename_table(
        "access_groups_old",
        "access_groups",
        schema="xi_back_2",
    )
    op.rename_table(
        "files_old",
        "files",
        schema="xi_back_2",
    )
    op.rename_table(
        "ydocs_old",
        "ydocs",
        schema="xi_back_2",
    )
