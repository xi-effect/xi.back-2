"""classroom_note_materials

Revision ID: 075
Revises: 074
Create Date: 2026-08-23 06:42:13.687953

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from migrations.enum_migrator import EnumMigrator

# revision identifiers, used by Alembic.
revision: str = "075"
down_revision: Union[str, None] = "074"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


material_access_kind_enum_migrator = EnumMigrator(
    enum_name="content_material_access_kind",
    old_members=("PERSONAL", "CLASSROOM"),
    new_members=("PERSONAL", "CLASSROOM", "CLASSROOM_NOTE"),
    column_paths=[
        ("xi_back_2", "materials", "access_kind"),
    ],
)


def upgrade() -> None:
    bind = op.get_bind()

    op.drop_index(
        "index_materials_classroom_id_updated_at",
        "materials",
        schema="xi_back_2",
    )
    op.drop_index(
        "index_materials_student_accessible_classroom_id_updated_at",
        "materials",
        schema="xi_back_2",
    )
    with material_access_kind_enum_migrator.upgrade(bind):
        pass
    op.alter_column(
        "materials",
        "name",
        existing_type=sa.VARCHAR(length=100),
        nullable=True,
        schema="xi_back_2",
    )
    op.create_index(
        "index_classroom_materials_pagination",
        "materials",
        ["classroom_id", "updated_at"],
        unique=False,
        schema="xi_back_2",
        postgresql_where=sa.text("access_kind = 'CLASSROOM'"),
    )
    op.create_index(
        "index_student_accessible_classroom_materials_pagination",
        "materials",
        ["classroom_id", "updated_at"],
        unique=False,
        schema="xi_back_2",
        postgresql_where=sa.text(
            "access_kind = 'CLASSROOM' AND student_access_mode IN ('READ_ONLY', 'READ_WRITE')"
        ),
    )
    op.create_index(
        "unique_index_classroom_note_materials_classroom_id",
        "materials",
        ["classroom_id"],
        unique=True,
        schema="xi_back_2",
        postgresql_where=sa.text("access_kind = 'CLASSROOM_NOTE'"),
    )


def downgrade() -> None:
    bind = op.get_bind()

    op.drop_index(
        "unique_index_classroom_note_materials_classroom_id",
        "materials",
        schema="xi_back_2",
    )
    op.drop_index(
        "index_student_accessible_classroom_materials_pagination",
        "materials",
        schema="xi_back_2",
    )
    op.drop_index(
        "index_classroom_materials_pagination",
        "materials",
        schema="xi_back_2",
    )

    metadata = sa.MetaData(schema="xi_back_2")
    Materials = sa.Table("materials", metadata, autoload_with=bind)
    YDocs = sa.Table("ydocs", metadata, autoload_with=bind)

    deleted_main_ydoc_ids = (
        bind.execute(
            sa.delete(Materials)
            .where(Materials.c.access_kind == "CLASSROOM_NOTE")
            .returning(Materials.c.main_ydoc_id)
        )
        .scalars()
        .all()
    )
    bind.execute(sa.delete(YDocs).where(YDocs.c.id.in_(deleted_main_ydoc_ids)))

    op.alter_column(
        "materials",
        "name",
        existing_type=sa.VARCHAR(length=100),
        nullable=False,
        schema="xi_back_2",
    )
    with material_access_kind_enum_migrator.downgrade(bind):
        pass
    op.create_index(
        "index_materials_classroom_id_updated_at",
        "materials",
        ["classroom_id", "updated_at"],
        unique=False,
        schema="xi_back_2",
        postgresql_where=sa.text("access_kind = 'CLASSROOM'"),
    )
    op.create_index(
        "index_materials_student_accessible_classroom_id_updated_at",
        "materials",
        ["classroom_id", "updated_at"],
        unique=False,
        schema="xi_back_2",
        postgresql_where=sa.text(
            "access_kind = 'CLASSROOM' AND student_access_mode IN ('READ_ONLY', 'READ_WRITE')"
        ),
    )
