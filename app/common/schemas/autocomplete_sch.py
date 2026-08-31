from enum import StrEnum, auto

from pydantic import BaseModel


class TagKind(StrEnum):
    SUBJECT = auto()
    GENERIC = auto()


class TagColor(StrEnum):
    RED = auto()
    ORANGE = auto()
    YELLOW = auto()
    GREEN = auto()
    TEAL = auto()
    BLUE = auto()
    INDIGO = auto()
    PURPLE = auto()
    PINK = auto()
    BROWN = auto()


class TagSchema(BaseModel):
    id: int
    name: str
    color: TagColor
