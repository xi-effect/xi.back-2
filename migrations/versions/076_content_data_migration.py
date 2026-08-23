"""content_data_migration

Revision ID: 076
Revises: 075
Create Date: 2026-08-23 11:33:50.794912

"""

import itertools
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence, Union
from uuid import UUID

import filetype  # type: ignore[import-untyped]
import sqlalchemy as sa
from alembic import op

from app.common.config import settings
from app.common.filetype_ext import (
    SUPPORTED_AUDIO_FORMATS,
    SUPPORTED_DOCUMENT_FORMATS,
    SUPPORTED_IMAGE_FORMATS,
    SUPPORTED_PRESENTATION_FORMATS,
)
from app.common.utils.datetime import datetime_utc_now
from migrations.file_processor import match_supported_files, save_image_to_webp

# revision identifiers, used by Alembic.
revision: str = "076"
down_revision: Union[str, None] = "075"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

OLD_FILE_KIND_TO_FOLDER: dict[str, Path] = {
    "UNCATEGORIZED": settings.storage_path / "uncategorized",
    "IMAGE": settings.storage_path / "images",
    "DOCUMENT": settings.storage_path / "documents",
    "AUDIO": settings.storage_path / "audios",
}

WEBP_CONTENT_TYPE = "image/webp"

OLD_FILE_KIND_TO_CONTENT_TYPE: dict[str, str] = {
    "IMAGE": WEBP_CONTENT_TYPE,
    "DOCUMENT": "application/pdf",
}

DEFAULT_CONTENT_TYPE = "application/octet-stream"

NEW_FILE_KIND_TO_SUPPORTED_FILETYPE: dict[str, list[filetype.Type]] = {
    "IMAGE": SUPPORTED_IMAGE_FORMATS,
    "DOCUMENT": SUPPORTED_DOCUMENT_FORMATS,
    "AUDIO": SUPPORTED_AUDIO_FORMATS,
    "PRESENTATION": SUPPORTED_PRESENTATION_FORMATS,
}

NEW_SUPPORTED_TYPES = list(
    itertools.chain.from_iterable(NEW_FILE_KIND_TO_SUPPORTED_FILETYPE.values())
)


def build_new_file_path(file_id: UUID) -> Path:
    hex_id = file_id.hex
    return settings.storage_path / "files" / hex_id[:2] / hex_id[2:4] / hex_id


def find_file_source_path(file_id: UUID, old_kind: str) -> Path | None:
    old_path = OLD_FILE_KIND_TO_FOLDER[old_kind] / file_id.hex
    if old_path.is_file():
        return old_path
    new_path = build_new_file_path(file_id)
    if new_path.is_file():
        return new_path
    return None


def upgrade() -> None:
    connection = op.get_bind()
    metadata = sa.MetaData(schema="xi_back_2")

    YDocsOld = sa.Table("ydocs_old", metadata, autoload_with=connection)
    FilesOld = sa.Table("files_old", metadata, autoload_with=connection)
    AccessGroups = sa.Table("access_groups", metadata, autoload_with=connection)
    AccessGroupFiles = sa.Table(
        "access_group_files", metadata, autoload_with=connection
    )
    MaterialsOld = sa.Table("materials_old", metadata, autoload_with=connection)
    ClassroomNotes = sa.Table("classroom_notes", metadata, autoload_with=connection)
    Classrooms = sa.Table("classrooms", metadata, autoload_with=connection)
    YDocs = sa.Table("ydocs", metadata, autoload_with=connection)
    Files = sa.Table("files", metadata, autoload_with=connection)
    YDocFiles = sa.Table("ydoc_files", metadata, autoload_with=connection)
    Materials = sa.Table("materials", metadata, autoload_with=connection)

    materials_join = MaterialsOld.join(
        AccessGroups,
        MaterialsOld.c.access_group_id == sa.cast(AccessGroups.c.id, sa.Text),
    )
    classroom_notes_join = ClassroomNotes.join(
        AccessGroups,
        ClassroomNotes.c.access_group_id == sa.cast(AccessGroups.c.id, sa.Text),
    )

    file_content_kind_materials_count = connection.execute(
        sa.select(sa.func.count())
        .select_from(MaterialsOld)
        .where(sa.cast(MaterialsOld.c.content_kind, sa.Text) == "FILE")
    ).scalar_one()
    if file_content_kind_materials_count != 0:
        raise RuntimeError(
            f"{file_content_kind_materials_count} materials have the legacy FILE content kind"
        )

    material_access_group_exists = sa.exists(
        sa.select(AccessGroups.c.id).where(
            MaterialsOld.c.access_group_id == sa.cast(AccessGroups.c.id, sa.Text)
        )
    )
    unmatched_materials_count = connection.execute(
        sa.select(sa.func.count())
        .select_from(MaterialsOld)
        .where(~material_access_group_exists)
    ).scalar_one()
    classroom_note_access_group_exists = sa.exists(
        sa.select(AccessGroups.c.id).where(
            ClassroomNotes.c.access_group_id == sa.cast(AccessGroups.c.id, sa.Text)
        )
    )
    unmatched_classroom_notes_count = connection.execute(
        sa.select(sa.func.count())
        .select_from(ClassroomNotes)
        .where(~classroom_note_access_group_exists)
    ).scalar_one()
    if unmatched_materials_count != 0 or unmatched_classroom_notes_count != 0:
        raise RuntimeError(
            f"{unmatched_materials_count} materials and {unmatched_classroom_notes_count}"
            " classroom notes have no access group"
        )

    mismatched_materials_count = connection.execute(
        sa.select(sa.func.count())
        .select_from(materials_join)
        .where(
            MaterialsOld.c.content_id != sa.cast(AccessGroups.c.main_ydoc_id, sa.Text)
        )
    ).scalar_one()
    mismatched_classroom_notes_count = connection.execute(
        sa.select(sa.func.count())
        .select_from(classroom_notes_join)
        .where(
            ClassroomNotes.c.ydoc_id != sa.cast(AccessGroups.c.main_ydoc_id, sa.Text)
        )
    ).scalar_one()
    if mismatched_materials_count != 0 or mismatched_classroom_notes_count != 0:
        raise RuntimeError(
            f"{mismatched_materials_count} materials and {mismatched_classroom_notes_count}"
            " classroom notes point at a ydoc other than their access group's main"
        )

    linked_ydoc_ids = sa.union_all(
        sa.select(AccessGroups.c.main_ydoc_id).select_from(materials_join),
        sa.select(AccessGroups.c.main_ydoc_id).select_from(classroom_notes_join),
    ).subquery()
    linked_count, distinct_linked_ydoc_count = connection.execute(
        sa.select(
            sa.func.count(),
            sa.func.count(sa.distinct(linked_ydoc_ids.c.main_ydoc_id)),
        ).select_from(linked_ydoc_ids)
    ).one()
    if linked_count != distinct_linked_ydoc_count:
        raise RuntimeError("multiple materials or classroom notes share one main ydoc")

    current_timestamp = datetime_utc_now()

    ydoc_columns = [
        YDocs.c.id,
        YDocs.c.owner_id,
        YDocs.c.content_kind,
        YDocs.c.content,
        YDocs.c.size_bytes,
        YDocs.c.created_at,
        YDocs.c.updated_at,
    ]
    material_access_kind = sa.cast(MaterialsOld.c.access_kind, sa.Text)
    material_ydoc_owner_id = sa.case(
        (material_access_kind == "TUTOR", MaterialsOld.c.tutor_id),
        else_=Classrooms.c.tutor_id,
    )
    material_ydocs_join = materials_join.join(
        YDocsOld,
        YDocsOld.c.id == AccessGroups.c.main_ydoc_id,
    ).outerjoin(
        Classrooms,
        Classrooms.c.id == MaterialsOld.c.classroom_id,
    )
    classroom_note_ydocs_join = classroom_notes_join.join(
        YDocsOld,
        YDocsOld.c.id == AccessGroups.c.main_ydoc_id,
    ).join(
        Classrooms,
        Classrooms.c.id == ClassroomNotes.c.classroom_id,
    )
    connection.execute(
        sa.insert(YDocs).from_select(
            ydoc_columns,
            sa.select(
                YDocsOld.c.id,
                material_ydoc_owner_id,
                sa.cast(
                    sa.cast(MaterialsOld.c.content_kind, sa.Text),
                    YDocs.c.content_kind.type,
                ),
                YDocsOld.c.content,
                sa.func.coalesce(sa.func.octet_length(YDocsOld.c.content), 0),
                MaterialsOld.c.created_at,
                MaterialsOld.c.updated_at,
            )
            .select_from(material_ydocs_join)
            .where(material_ydoc_owner_id.is_not(None)),
        )
    )
    connection.execute(
        sa.insert(YDocs).from_select(
            ydoc_columns,
            sa.select(
                YDocsOld.c.id,
                Classrooms.c.tutor_id,
                sa.cast(sa.literal("NOTE"), YDocs.c.content_kind.type),
                YDocsOld.c.content,
                sa.func.coalesce(sa.func.octet_length(YDocsOld.c.content), 0),
                sa.literal(current_timestamp),
                sa.literal(current_timestamp),
            ).select_from(classroom_note_ydocs_join),
        )
    )

    # the join onto the new ydocs keeps materials whose ydoc was skipped above out
    connection.execute(
        sa.insert(Materials).from_select(
            [
                Materials.c.id,
                Materials.c.access_kind,
                Materials.c.main_ydoc_id,
                Materials.c.name,
                Materials.c.updated_at,
                Materials.c.tutor_id,
                Materials.c.classroom_id,
                Materials.c.student_access_mode,
            ],
            sa.select(
                sa.func.gen_random_uuid(),
                sa.cast(
                    sa.case(
                        (material_access_kind == "TUTOR", "PERSONAL"),
                        else_=material_access_kind,
                    ),
                    Materials.c.access_kind.type,
                ),
                AccessGroups.c.main_ydoc_id,
                MaterialsOld.c.name,
                MaterialsOld.c.updated_at,
                MaterialsOld.c.tutor_id,
                MaterialsOld.c.classroom_id,
                sa.cast(
                    sa.cast(MaterialsOld.c.student_access_mode, sa.Text),
                    Materials.c.student_access_mode.type,
                ),
            ).select_from(
                materials_join.join(YDocs, YDocs.c.id == AccessGroups.c.main_ydoc_id)
            ),
        )
    )
    connection.execute(
        sa.insert(Materials).from_select(
            [
                Materials.c.id,
                Materials.c.access_kind,
                Materials.c.main_ydoc_id,
                Materials.c.updated_at,
                Materials.c.classroom_id,
            ],
            sa.select(
                sa.func.gen_random_uuid(),
                sa.cast(sa.literal("CLASSROOM_NOTE"), Materials.c.access_kind.type),
                AccessGroups.c.main_ydoc_id,
                sa.literal(current_timestamp),
                ClassroomNotes.c.classroom_id,
            ).select_from(
                classroom_notes_join.join(
                    YDocs, YDocs.c.id == AccessGroups.c.main_ydoc_id
                )
            ),
        )
    )

    # the earliest linked ydoc wins a shared file's owner; id breaks the ties
    # between classroom note ydocs, which share one timestamp
    file_rows = connection.execute(
        sa.select(
            FilesOld.c.id,
            FilesOld.c.name,
            sa.cast(FilesOld.c.kind, sa.Text).label("kind"),
            YDocs.c.owner_id,
        )
        .select_from(
            FilesOld.join(AccessGroupFiles, AccessGroupFiles.c.file_id == FilesOld.c.id)
            .join(AccessGroups, AccessGroups.c.id == AccessGroupFiles.c.access_group_id)
            .join(YDocs, YDocs.c.id == AccessGroups.c.main_ydoc_id)
        )
        .order_by(YDocs.c.created_at, YDocs.c.id)
    ).all()

    seen_file_ids: set[UUID] = set()
    file_data: list[dict[str, Any]] = []
    for file_row in file_rows:
        if file_row.id in seen_file_ids:
            continue
        seen_file_ids.add(file_row.id)

        source_path = find_file_source_path(file_row.id, file_row.kind)
        if source_path is None:
            continue

        source_stat = source_path.stat()
        content_type = (
            OLD_FILE_KIND_TO_CONTENT_TYPE.get(file_row.kind) or DEFAULT_CONTENT_TYPE
        )
        file_data.append(
            {
                "id": file_row.id,
                "owner_id": file_row.owner_id,
                "uploader_id": file_row.owner_id,
                "name": Path(file_row.name).stem,
                "extension": Path(file_row.name).suffix.lstrip("."),
                "kind": file_row.kind,
                "content_type": content_type,
                "size_bytes": source_stat.st_size,
                "created_at": datetime.fromtimestamp(
                    source_stat.st_mtime, tz=timezone.utc
                ),
            }
        )

    if file_rows and not file_data:
        raise RuntimeError(
            f"none of {len(seen_file_ids)} files were found in {settings.storage_path}"
        )

    if file_data:
        connection.execute(sa.insert(Files), file_data)

    # the joins onto the new ydocs and files keep links to skipped rows out
    connection.execute(
        sa.insert(YDocFiles).from_select(
            [YDocFiles.c.ydoc_id, YDocFiles.c.file_id],
            sa.select(AccessGroups.c.main_ydoc_id, AccessGroupFiles.c.file_id)
            .distinct()
            .select_from(
                AccessGroupFiles.join(
                    AccessGroups,
                    AccessGroups.c.id == AccessGroupFiles.c.access_group_id,
                )
                .join(YDocs, YDocs.c.id == AccessGroups.c.main_ydoc_id)
                .join(Files, Files.c.id == AccessGroupFiles.c.file_id)
            ),
        )
    )

    file_updates: list[dict[str, Any]] = []
    for file_data_row in file_data:
        old_path = (
            OLD_FILE_KIND_TO_FOLDER[file_data_row["kind"]] / file_data_row["id"].hex
        )
        new_path = build_new_file_path(file_data_row["id"])
        if old_path.is_file():
            new_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(old_path, new_path)

        file_type = match_supported_files(new_path, NEW_SUPPORTED_TYPES)
        if file_type is None:
            continue
        detected_kind = [
            kind
            for kind, types in NEW_FILE_KIND_TO_SUPPORTED_FILETYPE.items()
            if file_type in types
        ][0]

        new_kind = file_data_row["kind"]
        new_content_type = file_type.mime
        if file_data_row["kind"] == "UNCATEGORIZED":
            new_kind = detected_kind
            if detected_kind == "IMAGE" and file_type.mime != WEBP_CONTENT_TYPE:
                temporary_path = new_path.with_name(f"{new_path.name}.webp")
                save_image_to_webp(new_path, temporary_path)
                temporary_path.replace(new_path)
                new_content_type = WEBP_CONTENT_TYPE
        elif detected_kind != file_data_row["kind"]:
            continue
        if (
            new_kind == file_data_row["kind"]
            and new_content_type == file_data_row["content_type"]
        ):
            continue

        file_updates.append(
            {
                "updated_file_id": file_data_row["id"],
                "new_kind": new_kind,
                "new_content_type": new_content_type,
                "new_size_bytes": new_path.stat().st_size,
            }
        )

    if file_updates:
        connection.execute(
            sa.update(Files)
            .where(Files.c.id == sa.bindparam("updated_file_id"))
            .values(
                kind=sa.bindparam("new_kind"),
                content_type=sa.bindparam("new_content_type"),
                size_bytes=sa.bindparam("new_size_bytes"),
            ),
            file_updates,
        )


def downgrade() -> None:
    connection = op.get_bind()
    metadata = sa.MetaData(schema="xi_back_2")

    YDocsOld = sa.Table("ydocs_old", metadata, autoload_with=connection)
    FilesOld = sa.Table("files_old", metadata, autoload_with=connection)
    AccessGroups = sa.Table("access_groups", metadata, autoload_with=connection)
    YDocs = sa.Table("ydocs", metadata, autoload_with=connection)
    Files = sa.Table("files", metadata, autoload_with=connection)
    Materials = sa.Table("materials", metadata, autoload_with=connection)

    connection.execute(
        sa.delete(Materials).where(
            Materials.c.main_ydoc_id.in_(sa.select(AccessGroups.c.main_ydoc_id))
        )
    )
    connection.execute(sa.delete(Files).where(Files.c.id.in_(sa.select(FilesOld.c.id))))
    connection.execute(sa.delete(YDocs).where(YDocs.c.id.in_(sa.select(YDocsOld.c.id))))

    old_file_rows = connection.execute(
        sa.select(FilesOld.c.id, sa.cast(FilesOld.c.kind, sa.Text).label("kind"))
    ).all()
    for old_file_row in old_file_rows:
        new_path = build_new_file_path(old_file_row.id)
        if new_path.is_file():
            old_path = OLD_FILE_KIND_TO_FOLDER[old_file_row.kind] / old_file_row.id.hex
            old_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(new_path, old_path)
