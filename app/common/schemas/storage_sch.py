from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel


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
