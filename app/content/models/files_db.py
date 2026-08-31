from collections.abc import Sequence
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Annotated, ClassVar, Literal, Self
from uuid import UUID, uuid4

import aiofiles
from pydantic import AwareDatetime, BaseModel, Field
from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import DateTime, Enum, ForeignKey, Index, Select, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Mapped, mapped_column, relationship

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
    kinds: Annotated[
        set[FileKind] | None,
        Field(min_length=1, max_length=len(FileKind)),
    ] = None
    is_uploaded_by_owner: bool | None = None
    tag_ids: Annotated[set[int] | None, Field(min_length=1, max_length=5)] = None


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

    file_tags: Mapped[list["FileTag"]] = relationship(
        lazy="selectin", passive_deletes="all"
    )

    __table_args__ = (Index("index_files_owner_id_created_at", owner_id, created_at),)

    @property
    def tag_ids(self) -> list[int]:
        return [file_tag.tag_id for file_tag in self.file_tags]

    BaseResponseSchema = MappedModel.create(
        columns=[
            id,
            name,
            extension,
            kind,
            size_bytes,
            (created_at, AwareDatetime),
        ],
        properties=[tag_ids],
    )
    ResponseSchema = BaseResponseSchema.extend(columns=[content_type])
    TutorResponseSchema = BaseResponseSchema.extend(columns=[uploader_id])
    StudentResponseSchema = BaseResponseSchema.extend()

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
            file_tags=[],
        )
        file.path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(file.path, "wb") as f:
            await f.write(content)
        return file

    async def delete(self) -> None:
        self.path.unlink(missing_ok=True)
        await super().delete()

    @classmethod
    def select_by_search_params(
        cls,
        search_params: FileSearchRequestSchema,
    ) -> Select[tuple[Self]]:
        stmt = select(cls)

        if search_params.filters.kinds is not None:
            stmt = stmt.filter(cls.kind.in_(search_params.filters.kinds))

        if search_params.filters.is_uploaded_by_owner is not None:
            if search_params.filters.is_uploaded_by_owner:
                stmt = stmt.filter(cls.uploader_id == cls.owner_id)
            else:
                stmt = stmt.filter(cls.uploader_id != cls.owner_id)

        if search_params.filters.tag_ids is not None:
            for tag_id in search_params.filters.tag_ids:
                stmt = stmt.filter(
                    select(FileTag)
                    .filter(FileTag.file_id == cls.id, FileTag.tag_id == tag_id)
                    .exists()
                )

        if search_params.cursor is not None:
            stmt = stmt.filter(cls.created_at < search_params.cursor.created_at)

        return stmt.order_by(cls.created_at.desc()).limit(search_params.limit)

    @classmethod
    async def find_paginated_by_owner_id(
        cls,
        owner_id: int,
        search_params: FileSearchRequestSchema,
    ) -> Sequence[Self]:
        return await db.get_all(
            cls.select_by_search_params(search_params).filter_by(owner_id=owner_id)
        )

    @classmethod
    async def find_paginated_by_classroom_id(
        cls,
        classroom_id: int,
        search_params: FileSearchRequestSchema,
    ) -> Sequence[Self]:
        return await db.get_all(
            cls.select_by_search_params(search_params)
            .join(ClassroomFile)
            .filter(ClassroomFile.classroom_id == classroom_id)
        )


class ClassroomFile(Base):
    __tablename__ = "classroom_files"

    file_id: Mapped[UUID] = mapped_column(
        ForeignKey(File.id, ondelete="CASCADE"),
        primary_key=True,
    )
    classroom_id: Mapped[int] = mapped_column(primary_key=True, index=True)

    @classmethod
    async def find_first_by_ids(
        cls,
        file_id: UUID,
        classroom_id: int,
    ) -> Self | None:
        return await cls.find_first_by_kwargs(
            file_id=file_id,
            classroom_id=classroom_id,
        )

    @classmethod
    async def upsert_by_ids(cls, file_id: UUID, classroom_id: int) -> None:
        await db.session.execute(
            insert(cls)
            .values(file_id=file_id, classroom_id=classroom_id)
            .on_conflict_do_nothing()
        )

    @classmethod
    async def find_all_classroom_ids_by_file_id(cls, file_id: UUID) -> Sequence[int]:
        return await db.get_all_with_assumed_limit(
            select(cls.classroom_id)
            .filter_by(file_id=file_id)
            .order_by(cls.classroom_id),
            limit=100,
        )


class FileTag(Base):
    __tablename__ = "file_tags"

    max_count_per_file: ClassVar[int] = 5

    file_id: Mapped[UUID] = mapped_column(
        ForeignKey(File.id, ondelete="CASCADE"),
        primary_key=True,
    )
    tag_id: Mapped[int] = mapped_column(primary_key=True)

    @classmethod
    async def replace_all_by_file_id(
        cls,
        file_id: UUID,
        tag_ids: set[int],
    ) -> None:
        await cls.delete_by_kwargs(file_id=file_id)
        if len(tag_ids) != 0:
            await cls.create_batch(
                {"file_id": file_id, "tag_id": tag_id} for tag_id in tag_ids
            )
