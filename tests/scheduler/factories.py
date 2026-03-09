from datetime import timezone

from polyfactory import PostGenerated

from app.scheduler.models.event_schedules_db import (
    OnceEventSchedule,
    WeeklyEventSchedule,
)
from app.scheduler.models.events_db import ClassroomEvent
from tests.common.polyfactory_ext import BaseModelFactory


class ClassroomEventInputFactory(BaseModelFactory[ClassroomEvent.InputSchema]):
    __model__ = ClassroomEvent.InputSchema


class ClassroomEventInvalidTimeFrameInputFactory(
    BaseModelFactory[ClassroomEvent.InputSchema]
):
    __model__ = ClassroomEvent.InputSchema


class OnceEventScheduleInputFactory(BaseModelFactory[OnceEventSchedule.InputSchema]):
    __model__ = OnceEventSchedule.InputSchema


class WeeklyEventScheduleInputFactory(
    BaseModelFactory[WeeklyEventSchedule.InputSchema]
):
    __model__ = WeeklyEventSchedule.InputSchema
    day_of_week = PostGenerated(lambda _, values: values["starts_at"].isoweekday())

    valid_until = PostGenerated(
        lambda _, values: BaseModelFactory.__faker__.date_time_between(
            start_date=values["starts_at"], end_date="+120m", tzinfo=timezone.utc
        )
    )
