from enum import StrEnum


class StorageAccessGroupKind(StrEnum):
    BOARD_CHANNEL = "board-channel"
    PERSONAL = "personal"


class YDocAccessLevel(StrEnum):
    NO_ACCESS = "no-access"
    READ_ONLY = "read-only"
    READ_WRITE = "read-write"
