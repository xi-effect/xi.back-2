from enum import StrEnum


class AccessLevel(StrEnum):
    NO_ACCESS = "no-access"
    READ_ONLY = "read-only"
    READ_WRITE = "read-write"


class AccessGroupKind(StrEnum):
    BOARD_CHANNEL = "board-channel"
