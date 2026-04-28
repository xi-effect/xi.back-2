from datetime import datetime, timedelta
from typing import Annotated, ClassVar, Self

from fastapi import Query
from pydantic import AwareDatetime, BaseModel, field_validator, model_validator


class EventTimeFrameSchema(BaseModel):
    min_period_duration: ClassVar[timedelta] = timedelta(days=1)
    max_period_duration: ClassVar[timedelta] = timedelta(days=30)

    happens_after: AwareDatetime
    happens_before: AwareDatetime

    @classmethod
    @field_validator("happens_after", "happens_before", mode="after")
    def remove_microseconds_from_timestamps(cls, value: datetime) -> datetime:
        # TODO (170) replace with a reusable AwareDatetimeNoMS type (use better naming)
        return value.replace(microsecond=0)

    @model_validator(mode="after")
    def validate_happens_after_and_happens_before(self) -> Self:
        period_duration = self.happens_before - self.happens_after
        if period_duration < timedelta():
            raise ValueError("happens_before must be later in time than happens_after")
        if period_duration < self.min_period_duration:
            raise ValueError("happens_before is too close to happens_after")
        if period_duration > self.max_period_duration:
            raise ValueError(
                "happens_before is too far in the future from happens_after"
            )
        return self


EventTimeFrameQuery = Annotated[EventTimeFrameSchema, Query()]
