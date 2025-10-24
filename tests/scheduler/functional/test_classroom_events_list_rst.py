from collections.abc import AsyncIterator
from datetime import datetime, timedelta, timezone
from typing import Literal

import pytest
from faker import Faker
from starlette.testclient import TestClient

from app.scheduler.models.events_db import ClassroomEvent
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_response
from tests.scheduler.factories import ClassroomEventInputFactory

pytestmark = pytest.mark.anyio

CLASSROOM_EVENT_LIST_SIZE = 6


@pytest.fixture()
async def classroom_events(
    active_session: ActiveSession,
    faker: Faker,
    classroom_id: int,
) -> AsyncIterator[list[ClassroomEvent]]:
    classroom_events: list[ClassroomEvent] = []
    start_datetime: datetime = faker.date_time_between(tzinfo=timezone.utc)

    async with active_session():
        for _ in range(CLASSROOM_EVENT_LIST_SIZE):
            end_datetime: datetime = (
                start_datetime
                + timedelta(minutes=10)
                + faker.time_delta(end_datetime="+120m")
            )
            classroom_events.append(
                await ClassroomEvent.create(
                    **ClassroomEventInputFactory.build_python(
                        starts_at=start_datetime,
                        ends_at=end_datetime,
                    ),
                    classroom_id=classroom_id,
                )
            )
            start_datetime = end_datetime + faker.time_delta(end_datetime="+360m")

    classroom_events.sort(
        key=lambda classroom_event: classroom_event.starts_at, reverse=True
    )

    yield classroom_events

    async with active_session():
        for classroom_event in classroom_events:
            await classroom_event.delete()


classroom_events_list_request_parametrization = pytest.mark.parametrize(
    ("index_happens_before", "index_happens_after"),
    [
        pytest.param(None, None, id="start_to_end"),
        pytest.param(None, CLASSROOM_EVENT_LIST_SIZE // 2, id="start_to_middle"),
        pytest.param(CLASSROOM_EVENT_LIST_SIZE // 2, None, id="middle_to_end"),
        pytest.param(None, 0, id="before_the_start"),
        pytest.param(-1, None, id="after_the_end"),
    ],
)


@classroom_events_list_request_parametrization
@pytest.mark.parametrize(
    "role_type",
    [
        pytest.param("tutor", id="tutor"),
        pytest.param("student", id="student"),
    ],
)
async def test_tutor_classroom_events_listing(
    faker: Faker,
    tutor_client: TestClient,
    classroom_id: int,
    classroom_events: list[ClassroomEvent],
    index_happens_before: int | None,
    index_happens_after: int | None,
    role_type: Literal["tutor", "student"],
) -> None:
    happens_after: datetime = (
        faker.date_time_between(
            end_date=classroom_events[0].ends_at, tzinfo=timezone.utc
        )
        if index_happens_after is None
        else classroom_events[index_happens_after].ends_at
    )
    happens_before: datetime = (
        faker.date_time_between(
            start_date=classroom_events[-1].starts_at, tzinfo=timezone.utc
        )
        if index_happens_before is None
        else classroom_events[index_happens_before].starts_at
    )

    assert_response(
        tutor_client.get(
            f"/api/protected/scheduler-service/roles/{role_type}/classrooms/{classroom_id}/events/",
            params={
                "happens_after": happens_after.isoformat(),
                "happens_before": happens_before.isoformat(),
            },
        ),
        expected_json=[
            ClassroomEvent.ResponseSchema.model_validate(
                classroom_event, from_attributes=True
            )
            for classroom_event in classroom_events
            if classroom_event.starts_at < happens_before
            and classroom_event.ends_at > happens_after
        ],
    )
