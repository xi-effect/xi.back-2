from collections.abc import AsyncIterator, Sequence
from datetime import datetime, timedelta, timezone

import pytest
from faker import Faker
from starlette.testclient import TestClient

from app.scheduler.models.events_db import Event
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_response
from tests.scheduler.factories import EventInputFactory

pytestmark = pytest.mark.anyio

EVENT_LIST_SIZE = 6


@pytest.fixture()
async def events(
    active_session: ActiveSession, faker: Faker
) -> AsyncIterator[Sequence[Event]]:
    events: list[Event] = []
    start_datetime: datetime = faker.date_time_between(tzinfo=timezone.utc)
    async with active_session():
        for _ in range(EVENT_LIST_SIZE):
            end_datetime: datetime = (
                start_datetime
                + timedelta(minutes=10)
                + faker.time_delta(end_datetime="+120m")
            )
            events.append(
                await Event.create(
                    **EventInputFactory.build_python(
                        starts_at=start_datetime, ends_at=end_datetime
                    )
                )
            )
            start_datetime = end_datetime + faker.time_delta(end_datetime="+360m")

    events.sort(key=lambda event: event.starts_at, reverse=True)

    yield events

    async with active_session():
        for event in events:
            await event.delete()


@pytest.mark.parametrize(
    ("index_happens_before", "index_happens_after"),
    [
        pytest.param(None, None, id="start_to_end"),
        pytest.param(None, EVENT_LIST_SIZE // 2, id="start_to_middle"),
        pytest.param(EVENT_LIST_SIZE // 2, None, id="middle_to_end"),
        pytest.param(None, 0, id="before_the_start"),
        pytest.param(-1, None, id="after_the_end"),
    ],
)
async def test_events_listing(
    faker: Faker,
    mub_client: TestClient,
    events: list[Event],
    index_happens_before: int | None,
    index_happens_after: int | None,
) -> None:
    happens_after: datetime = (
        faker.date_time_between(end_date=events[0].ends_at, tzinfo=timezone.utc)
        if index_happens_after is None
        else events[index_happens_after].ends_at
    )

    happens_before: datetime = (
        faker.date_time_between(start_date=events[-1].starts_at, tzinfo=timezone.utc)
        if index_happens_before is None
        else events[index_happens_before].starts_at
    )

    assert_response(
        mub_client.get(
            "/mub/scheduler-service/events/",
            params={
                "happens_after": happens_after.isoformat(),
                "happens_before": happens_before.isoformat(),
            },
        ),
        expected_json=[
            Event.ResponseSchema.model_validate(event)
            for event in events
            if event.starts_at < happens_before and event.ends_at > happens_after
        ],
    )


@pytest.mark.parametrize(
    "is_equal",
    [
        pytest.param(True, id="after_equal_before"),
        pytest.param(False, id="after_greater_than_before"),
    ],
)
async def test_events_listing_happens_after_ge_happens_before(
    faker: Faker, mub_client: TestClient, events: list[Event], is_equal: bool
) -> None:
    happens_after: datetime = faker.date_time_between(
        start_date="-25y",  # start_date is needed for happens_before to have room for generation
        tzinfo=timezone.utc,
    )

    happens_before: datetime = (
        happens_after
        if is_equal
        else faker.date_time_between(end_date=happens_after, tzinfo=timezone.utc)
    )

    assert_response(
        mub_client.get(
            "/mub/scheduler-service/events/",
            params={
                "happens_after": happens_after.isoformat(),
                "happens_before": happens_before.isoformat(),
            },
        ),
        expected_code=422,
        expected_json={
            "detail": "Parameter happens_before must be later in time than happens_after"
        },
    )
