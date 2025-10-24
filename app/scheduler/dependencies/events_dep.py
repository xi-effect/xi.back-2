from typing import Annotated, Self

from fastapi import Query
from pydantic import AwareDatetime, BaseModel, model_validator


class EventTimeFrameSchema(BaseModel):
    happens_after: AwareDatetime
    happens_before: AwareDatetime

    @model_validator(mode="after")
    def validate_happens_after_and_happens_before(self) -> Self:
        if self.happens_after >= self.happens_before:
            raise ValueError(
                "parameter happens_before must be later in time than happens_after"
            )
        return self


EventTimeFrameQuery = Annotated[EventTimeFrameSchema, Query()]
