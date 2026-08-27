from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel


class YDocAccessLevel(StrEnum):
    NO_ACCESS = "no-access"
    READ_ONLY = "read-only"
    READ_WRITE = "read-write"


class ContentTokenPayloadSchema(BaseModel):
    material_id: UUID
    ydoc_id: UUID
    user_id: int | None

    can_upload_files: bool
    can_read_files: bool

    ydoc_access_level: YDocAccessLevel


class ContentYDocItemSchema(BaseModel):
    ydoc_id: UUID
    content_token: str
