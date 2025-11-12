from enum import StrEnum, auto

from pydantic import BaseModel


class EmailMessageKind(StrEnum):
    EMAIL_CONFIRMATION_V1 = auto()
    EMAIL_CHANGE_V1 = auto()
    PASSWORD_RESET_V1 = auto()


class EmailMessageInputSchema(BaseModel):
    kind: EmailMessageKind
    recipient_email: str
    token: str  # TODO pass actual data instead
