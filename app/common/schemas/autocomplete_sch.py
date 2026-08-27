from enum import StrEnum, auto

from pydantic import BaseModel


class TagKind(StrEnum):
    SUBJECT = auto()


class TagSchema(BaseModel):
    id: int
    name: str
