from datetime import timedelta
from typing import Final

MIN_EVENT_INSTANCE_DURATION: Final[timedelta] = timedelta()
MAX_EVENT_INSTANCE_DURATION: Final[timedelta] = timedelta(hours=12)
MAX_TIMEDELTA_TO_THE_PAST: Final[timedelta] = timedelta(days=-370)
MAX_TIMEDELTA_TO_THE_FUTURE: Final[timedelta] = timedelta(days=370)
