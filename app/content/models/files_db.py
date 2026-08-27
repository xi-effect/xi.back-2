from collections.abc import Sequence
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Annotated, Literal, Self
from uuid import UUID, uuid4

import aiofiles
from pydantic import AwareDatetime, BaseModel, Field
from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import DateTime, Enum, Index, select
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base, settings
from app.common.sqlalchemy_ext import db
from app.common.utils.datetime import datetime_utc_now


class FileKind(StrEnum):
    UNCATEGORIZED = "uncategorized"
    IMAGE = "image"
    DOCUMENT = "document"
    AUDIO = "audio"
    PRESENTATION = "presentation"


ContentDisposition = Literal["inline", "attachment"]

FILE_KIND_TO_CONTENT_DISPOSITION: dict[FileKind, ContentDisposition] = {
    FileKind.UNCATEGORIZED: "attachment",
    FileKind.IMAGE: "inline",
    FileKind.DOCUMENT: "inline",
    FileKind.AUDIO: "inline",
    FileKind.PRESENTATION: "attachment",
}


class FileCursorSchema(BaseModel):
    created_at: AwareDatetime


class FileFiltersSchema(BaseModel):
    pass


class FileSearchRequestSchema(BaseModel):
    cursor: FileCursorSchema | None = None
    limit: Annotated[int, Field(gt=0, lt=100)] = 12
    filters: FileFiltersSchema


class File(Base):
    __tablename__ = "files"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[int] = mapped_column()
    uploader_id: Mapped[int] = mapped_column()

    name: Mapped[str] = mapped_column()
    extension: Mapped[str] = mapped_column()
    kind: Mapped[FileKind] = mapped_column(Enum(FileKind, name="content_file_kind"))
    content_type: Mapped[str] = mapped_column()
    size_bytes: Mapped[int] = mapped_column()

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime_utc_now
    )

    __table_args__ = (Index("index_files_owner_id_created_at", owner_id, created_at),)

    BaseResponseSchema = MappedModel.create(
        columns=[
            id,
            name,
            extension,
            kind,
            size_bytes,
            (created_at, AwareDatetime),
        ]
    )
    ResponseSchema = BaseResponseSchema.extend(columns=[content_type])
    LibraryResponseSchema = BaseResponseSchema.extend(columns=[uploader_id])

    @property
    def path(self) -> Path:
        hex_id = self.id.hex
        return settings.storage_path / "files" / hex_id[:2] / hex_id[2:4] / hex_id

    @property
    def filename(self) -> str:
        return self.name if self.extension == "" else f"{self.name}.{self.extension}"

    @property
    def content_disposition(self) -> ContentDisposition:
        return FILE_KIND_TO_CONTENT_DISPOSITION.get(self.kind, "attachment")

    @classmethod
    async def create_with_content(
        cls,
        content: bytes,
        owner_id: int,
        uploader_id: int,
        name: str,
        extension: str,
        file_kind: FileKind,
        content_type: str,
    ) -> Self:
        file = await cls.create(
            owner_id=owner_id,
            uploader_id=uploader_id,
            name=name,
            extension=extension,
            kind=file_kind,
            content_type=content_type,
            size_bytes=len(content),
        )
        file.path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(file.path, "wb") as f:
            await f.write(content)
        return file

    async def delete(self) -> None:
        self.path.unlink(missing_ok=True)
        await super().delete()

    @classmethod
    async def find_paginated_by_owner_id(
        cls,
        owner_id: int,
        search_params: FileSearchRequestSchema,
    ) -> Sequence[Self]:
        stmt = select(cls).filter_by(owner_id=owner_id)

        if search_params.cursor is not None:
            stmt = stmt.filter(cls.created_at < search_params.cursor.created_at)

        return await db.get_all(
            stmt.order_by(cls.created_at.desc()).limit(search_params.limit)
        )
