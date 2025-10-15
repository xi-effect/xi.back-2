from enum import StrEnum

from pydantic import BaseModel


class UserContactKind(StrEnum):
    PERSONAL_TELEGRAM = "personal-telegram"


class UserContactSchema(BaseModel):
    kind: UserContactKind
    link: str
    title: str
    is_public: bool
