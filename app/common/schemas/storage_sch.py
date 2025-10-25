from enum import StrEnum, auto
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class StorageAccessGroupKind(StrEnum):
    BOARD_CHANNEL = "board-channel"
    PERSONAL = "personal"


class YDocAccessLevel(StrEnum):
    NO_ACCESS = "no-access"
    READ_ONLY = "read-only"
    READ_WRITE = "read-write"


class StorageTokenPayloadSchema(BaseModel):
    access_group_id: UUID
    user_id: int | None

    can_upload_files: bool
    can_read_files: bool

    ydoc_access_level: YDocAccessLevel


class StorageItemKind(StrEnum):
    FILE = auto()
    YDOC = auto()


class StorageBaseItemSchema(BaseModel):
    access_group_id: UUID
    storage_token: str


class StorageFileItemSchema(StorageBaseItemSchema):
    kind: Literal[StorageItemKind.FILE] = StorageItemKind.FILE
    file_id: UUID


class StorageYDocItemSchema(StorageBaseItemSchema):
    kind: Literal[StorageItemKind.YDOC] = StorageItemKind.YDOC
    ydoc_id: UUID


StorageItemSchema = Annotated[
    StorageFileItemSchema | StorageYDocItemSchema,
    Field(discriminator="kind"),
]
