from datetime import timezone

from polyfactory import PostGenerated

from app.scheduler.models.events_db import ClassroomEvent
from tests.common.polyfactory_ext import BaseModelFactory


class ClassroomEventInputFactory(BaseModelFactory[ClassroomEvent.InputSchema]):
    __model__ = ClassroomEvent.InputSchema

    ends_at = PostGenerated(
        lambda _, values: BaseModelFactory.__faker__.date_time_between(
            start_date=values["starts_at"], end_date="+120m", tzinfo=timezone.utc
        )
    )


class ClassroomEventInvalidTimeFrameInputFactory(
    BaseModelFactory[ClassroomEvent.InputSchema]
):
    __model__ = ClassroomEvent.InputSchema

    ends_at = PostGenerated(
        lambda _, values: BaseModelFactory.__faker__.date_time(
            end_datetime=values["starts_at"], tzinfo=timezone.utc
        )
    )
