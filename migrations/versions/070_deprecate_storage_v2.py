"""deprecate_storage_v2

Revision ID: 070
Revises: 069
Create Date: 2026-08-19 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "070"
down_revision: Union[str, None] = "069"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
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
        "fk_access_groups_main_ydoc_id_ydocs",
        table_name="access_groups",
        schema="xi_back_2",
    )
    op.drop_constraint(
        "fk_access_group_files_file_id_files",
        table_name="access_group_files",
        schema="xi_back_2",
    )
    op.drop_constraint(
        "pk_files",
        "files_old",
        schema="xi_back_2",
    )
    op.drop_constraint(
        "pk_ydocs",
        "ydocs_old",
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
    op.create_foreign_key(
        "fk_access_groups_main_ydoc_id_ydocs_old",
        source_table="access_groups",
        referent_table="ydocs_old",
        local_cols=["main_ydoc_id"],
        remote_cols=["id"],
        source_schema="xi_back_2",
        referent_schema="xi_back_2",
    )
    op.create_foreign_key(
        "fk_access_group_files_file_id_files_old",
        source_table="access_group_files",
        referent_table="files_old",
        local_cols=["file_id"],
        remote_cols=["id"],
        source_schema="xi_back_2",
        referent_schema="xi_back_2",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_access_group_files_file_id_files_old",
        table_name="access_group_files",
        schema="xi_back_2",
    )
    op.drop_constraint(
        "fk_access_groups_main_ydoc_id_ydocs_old",
        table_name="access_groups",
        schema="xi_back_2",
    )
    op.drop_constraint(
        "pk_ydocs_old",
        "ydocs_old",
        schema="xi_back_2",
    )
    op.drop_constraint(
        "pk_files_old",
        "files_old",
        schema="xi_back_2",
    )

    op.create_primary_key(
        "pk_ydocs",
        "ydocs_old",
        ["id"],
        schema="xi_back_2",
    )
    op.create_primary_key(
        "pk_files",
        "files_old",
        ["id"],
        schema="xi_back_2",
    )
    op.create_foreign_key(
        "fk_access_group_files_file_id_files",
        source_table="access_group_files",
        referent_table="files_old",
        local_cols=["file_id"],
        remote_cols=["id"],
        source_schema="xi_back_2",
        referent_schema="xi_back_2",
    )
    op.create_foreign_key(
        "fk_access_groups_main_ydoc_id_ydocs",
        source_table="access_groups",
        referent_table="ydocs_old",
        local_cols=["main_ydoc_id"],
        remote_cols=["id"],
        source_schema="xi_back_2",
        referent_schema="xi_back_2",
    )

    op.rename_table(
        "ydocs_old",
        "ydocs",
        schema="xi_back_2",
    )
    op.rename_table(
        "files_old",
        "files",
        schema="xi_back_2",
    )
