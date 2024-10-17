from enum import StrEnum
from pathlib import Path
from typing import Literal
from uuid import UUID, uuid4

from pydantic_marshals.sqlalchemy import MappedModel
from sqlalchemy import Enum
from sqlalchemy.orm import Mapped, mapped_column

from app.common.config import Base, settings


class FileKind(StrEnum):
    ATTACHMENT = "attachment"
    IMAGE = "image"


ContentDisposition = Literal["inline", "attachment"]

FILE_KIND_TO_FOLDER: dict[FileKind, str] = {
    FileKind.ATTACHMENT: "files",
    FileKind.IMAGE: "images",
}
FILE_KIND_TO_MEDIA_TYPE: dict[FileKind, str | None] = {
    FileKind.ATTACHMENT: None,
    FileKind.IMAGE: "image/webp",
}
FILE_KIND_TO_CONTENT_DISPOSITION: dict[FileKind, ContentDisposition] = {
    FileKind.ATTACHMENT: "attachment",
    FileKind.IMAGE: "inline",
}


class File(Base):
    __tablename__ = "files"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column()
    kind: Mapped[FileKind] = mapped_column(Enum(FileKind))

    creator_user_id: Mapped[int | None] = mapped_column()

    ResponseSchema = MappedModel.create(columns=[id, name, kind, creator_user_id])

    @property
    def path(self) -> Path:
        return settings.storage_path / FILE_KIND_TO_FOLDER[self.kind] / self.id.hex

    @property
    def media_type(self) -> str | None:
        return FILE_KIND_TO_MEDIA_TYPE[self.kind]

    @property
    def content_disposition(self) -> ContentDisposition:
        return FILE_KIND_TO_CONTENT_DISPOSITION.get(self.kind, "attachment")

    async def delete(self) -> None:
        self.path.unlink(missing_ok=True)
        await super().delete()
