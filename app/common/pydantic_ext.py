from datetime import datetime
from typing import TYPE_CHECKING, Annotated

from pydantic import AwareDatetime, FutureDatetime, PastDatetime

if TYPE_CHECKING:
    PastAwareDatetime = Annotated[datetime, ...]
    FutureAwareDatetime = Annotated[datetime, ...]
else:
    PastAwareDatetime = type(
        "PastAwareDatetime",
        (PastDatetime, AwareDatetime),
        {},
    )
    FutureAwareDatetime = type(
        "FutureAwareDatetime",
        (FutureDatetime, AwareDatetime),
        {},
    )
