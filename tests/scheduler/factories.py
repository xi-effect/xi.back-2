from datetime import timezone

from polyfactory import PostGenerated

from app.scheduler.models.events_db import Event
from tests.common.polyfactory_ext import BaseModelFactory


class EventInputFactory(BaseModelFactory[Event.InputSchema]):
    __model__ = Event.InputSchema
    ends_at = PostGenerated(
        lambda _, values: BaseModelFactory.__faker__.date_time_between(
            start_date=values["starts_at"], end_date="+120m", tzinfo=timezone.utc
        )
    )
