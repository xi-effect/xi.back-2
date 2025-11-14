from enum import StrEnum, auto

from pydantic import AwareDatetime, BaseModel, Field

from app.common.utils.datetime import datetime_utc_now


class DatalakeEventKind(StrEnum):
    OPEN_SOCKETIO_CONNECTION = auto()


class DatalakeEventInputSchema(BaseModel):
    kind: DatalakeEventKind
    user_id: int
    recorded_at: AwareDatetime = Field(default_factory=datetime_utc_now)
