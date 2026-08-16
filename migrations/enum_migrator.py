from collections.abc import Iterator
from contextlib import contextmanager

import sqlalchemy as sa
from alembic import op


class EnumMigrator:
    def __init__(
        self,
        enum_name: str,
        old_members: tuple[str, ...],
        new_members: tuple[str, ...],
        column_paths: list[tuple[str, str, str]],
    ) -> None:
        self.enum_name = enum_name
        self.column_paths = column_paths

        all_members = tuple(set(old_members).union(new_members))
        self.old_enum = sa.Enum(*old_members, name=enum_name)
        self.tmp_enum = sa.Enum(*all_members, name=f"tmp_{enum_name}")
        self.new_enum = sa.Enum(*new_members, name=enum_name)

    def migrate_to_enum(self, enum: sa.Enum) -> None:
        for schema_name, table_name, column_name in self.column_paths:
            op.alter_column(
                table_name,
                column_name,
                schema=schema_name,
                type_=enum,
                postgresql_using=f"{column_name}::text::{enum.name}",
            )

    @contextmanager
    def migrate(
        self, bind: sa.Connection, source_enum: sa.Enum, target_enum: sa.Enum
    ) -> Iterator[None]:
        self.tmp_enum.create(bind=bind)
        self.migrate_to_enum(enum=self.tmp_enum)
        source_enum.drop(bind=bind)

        yield

        target_enum.create(bind=bind)
        self.migrate_to_enum(enum=target_enum)
        self.tmp_enum.drop(bind=bind)

    @contextmanager
    def upgrade(self, bind: sa.Connection) -> Iterator[None]:
        with self.migrate(bind, self.old_enum, self.new_enum):
            yield

    @contextmanager
    def downgrade(self, bind: sa.Connection) -> Iterator[None]:
        with self.migrate(bind, self.new_enum, self.old_enum):
            yield
