from collections.abc import AsyncIterator
from datetime import datetime, timedelta, timezone
from typing import Literal

import pytest
from faker import Faker
from pytest_lazy_fixtures import lf
from starlette import status
from starlette.testclient import TestClient

from app.scheduler.models.events_db import ClassroomEvent
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_response
from tests.scheduler.factories import ClassroomEventInputFactory

pytestmark = pytest.mark.anyio

CLASSROOM_EVENT_LIST_SIZE = 6


@pytest.fixture()
async def classroom_events(
    faker: Faker,
    active_session: ActiveSession,
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
        pytest.param(None, None, id="start-to-end"),
        pytest.param(None, CLASSROOM_EVENT_LIST_SIZE // 2, id="start-to-middle"),
        pytest.param(CLASSROOM_EVENT_LIST_SIZE // 2, None, id="middle-to-end"),
        pytest.param(None, 0, id="before-the-start"),
        pytest.param(-1, None, id="after-the-end"),
    ],
)


classroom_events_role_parametrization = pytest.mark.parametrize(
    ("authorized_client", "role_type"),
    [
        pytest.param(lf("tutor_client"), "tutor", id="tutor"),
        pytest.param(lf("student_client"), "student", id="student"),
    ],
)


@classroom_events_list_request_parametrization
@classroom_events_role_parametrization
async def test_tutor_classroom_events_listing(
    faker: Faker,
    classroom_id: int,
    classroom_events: list[ClassroomEvent],
    index_happens_before: int | None,
    index_happens_after: int | None,
    authorized_client: TestClient,
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
        authorized_client.get(
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


@pytest.mark.parametrize(
    "is_equal",
    [
        pytest.param(True, id="after-equal-before"),
        pytest.param(False, id="after-greater-than-before"),
    ],
)
@classroom_events_role_parametrization
async def test_classroom_events_listing_happens_after_ge_happens_before(
    faker: Faker,
    classroom_id: int,
    classroom_events: list[ClassroomEvent],
    is_equal: bool,
    authorized_client: TestClient,
    role_type: Literal["tutor", "student"],
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
        authorized_client.get(
            f"/api/protected/scheduler-service/roles/{role_type}"
            f"/classrooms/{classroom_id}/events/",
            params={
                "happens_after": happens_after.isoformat(),
                "happens_before": happens_before.isoformat(),
            },
        ),
        expected_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        expected_json={
            "detail": [
                {
                    "type": "value_error",
                    "loc": ["query"],
                    "msg": "Value error, parameter happens_before must be later in time than happens_after",
                },
            ]
        },
    )
