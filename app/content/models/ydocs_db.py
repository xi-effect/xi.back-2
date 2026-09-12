from collections.abc import AsyncIterable, AsyncIterator
from datetime import datetime
from enum import StrEnum, auto
from pathlib import Path
from typing import Final, Self, cast
from uuid import UUID, uuid4

import aiofiles
from aiofiles.os import replace
from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import DateTime, Enum, LargeBinary, insert, select
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base, settings
from app.common.sqlalchemy_ext import db
from app.common.utils.datetime import datetime_utc_now

CONTENT_COPY_CHUNK_SIZE: Final[int] = 64 * 1024


async def read_file_in_chunks(path: Path) -> AsyncIterator[bytes]:
    async with aiofiles.open(path, "rb") as file:
        while True:
            chunk = await file.read(CONTENT_COPY_CHUNK_SIZE)
            if len(chunk) == 0:
                break
            yield chunk


async def write_file_from_chunks(path: Path, chunks: AsyncIterable[bytes]) -> None:
    async with aiofiles.open(path, "wb") as file:
        async for chunk in chunks:
            await file.write(chunk)


class YDocContentKind(StrEnum):
    NOTE = auto()
    BOARD = auto()


class YDoc(Base):
    __tablename__ = "ydocs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[int] = mapped_column(index=True)

    content_kind: Mapped[YDocContentKind] = mapped_column(
        Enum(YDocContentKind, name="content_ydoc_kind")
    )
    content: Mapped[bytes | None] = mapped_column(
        LargeBinary, default=None, deferred=True
    )
    size_bytes: Mapped[int] = mapped_column(default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime_utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime_utc_now
    )

    ResponseSchema = MappedModel.create(
        columns=[id, owner_id, content_kind, size_bytes, created_at, updated_at]
    )

    @property
    def path(self) -> Path:
        hex_id = self.id.hex
        return settings.storage_path / "ydocs" / hex_id[:2] / hex_id[2:4] / hex_id

    async def duplicate(self) -> Self:
        stmt = (
            insert(type(self))
            .from_select(
                [type(self).owner_id, type(self).content_kind, type(self).size_bytes],
                (
                    select(
                        type(self).owner_id,
                        type(self).content_kind,
                        type(self).size_bytes,
                    )
                    .select_from(type(self))
                    .filter_by(id=self.id)
                ),
            )
            .returning(type(self))
        )
        ydoc = (await db.session.execute(stmt)).scalar_one()

        if self.path.exists():
            ydoc.path.parent.mkdir(parents=True, exist_ok=True)
            await write_file_from_chunks(
                path=ydoc.path,
                chunks=read_file_in_chunks(self.path),
            )

        return ydoc

    async def write_content(
        self,
        gzipped_content_stream: AsyncIterable[bytes],
    ) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path: Path | None = None
        try:
            async with aiofiles.tempfile.NamedTemporaryFile(
                "wb", dir=self.path.parent, delete=False
            ) as temporary_file:
                temporary_path = Path(cast(str, temporary_file.name))
                async for chunk in gzipped_content_stream:
                    await temporary_file.write(chunk)
            await replace(temporary_path, self.path)
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

    def delete_content(self) -> None:
        self.path.unlink(missing_ok=True)

    async def delete(self) -> None:
        self.delete_content()
        await super().delete()
