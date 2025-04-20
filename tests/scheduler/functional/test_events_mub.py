from datetime import datetime, timezone
from typing import Any

import pytest
from faker import Faker
from pydantic_marshals.contains import assert_contains
from starlette.testclient import TestClient

from app.scheduler.models.events_db import Event
from tests.common.active_session import ActiveSession
from tests.common.assert_contains_ext import assert_nodata_response, assert_response
from tests.common.polyfactory_ext import BaseModelFactory
from tests.common.types import AnyJSON
from tests.scheduler.factories import EventInputFactory

pytestmark = pytest.mark.anyio


async def test_event_creation(
    active_session: ActiveSession,
    mub_client: TestClient,
) -> None:
    event_input_data = EventInputFactory.build_json()

    event_id = assert_response(
        mub_client.post("/mub/scheduler-service/events/", json=event_input_data),
        expected_code=201,
        expected_json={
            **event_input_data,
            "id": int,
        },
    ).json()["id"]

    async with active_session():
        event = await Event.find_first_by_id(event_id)
        assert event is not None
        await event.delete()


async def test_event_creation_end_time_le_start_time(
    faker: Faker,
    mub_client: TestClient,
) -> None:
    start_datetime: datetime = faker.date_time_between(tzinfo=timezone.utc)
    end_datetime: datetime = faker.date_time_between(
        end_date=start_datetime, tzinfo=timezone.utc
    )
    invalid_event_input_data = EventInputFactory.build_json(
        starts_at=start_datetime, ends_at=end_datetime
    )
    assert_contains(
        mub_client.post(
            "/mub/scheduler-service/events/", json=invalid_event_input_data
        ).json(),
        {
            "detail": [
                {
                    "type": "value_error",
                    "loc": ["body"],
                    "msg": "Value error, the start time of an event cannot be greater than or equal to the end time",
                }
            ]
        },
    )


async def test_event_retrieving(
    mub_client: TestClient,
    event: Event,
    event_data: AnyJSON,
) -> None:
    assert_response(
        mub_client.get(f"/mub/scheduler-service/events/{event.id}/"),
        expected_json=event_data,
    )


async def test_event_updating(
    mub_client: TestClient,
    event: Event,
) -> None:
    event_input_data = EventInputFactory.build_json()
    assert_response(
        mub_client.put(
            f"/mub/scheduler-service/events/{event.id}/",
            json=event_input_data,
        ),
        expected_json={**event_input_data, "id": event.id},
    )


async def test_event_deleting(
    active_session: ActiveSession,
    mub_client: TestClient,
    event: Event,
) -> None:
    assert_nodata_response(
        mub_client.delete(f"/mub/scheduler-service/events/{event.id}/")
    )

    async with active_session():
        assert await Event.find_first_by_id(event.id) is None


@pytest.mark.parametrize(
    ("method", "body_factory"),
    [
        pytest.param("GET", None, id="retrieve"),
        pytest.param("PUT", EventInputFactory, id="update"),
        pytest.param("DELETE", None, id="delete"),
    ],
)
async def test_event_not_finding(
    active_session: ActiveSession,
    mub_client: TestClient,
    deleted_event_id: Event,
    method: str,
    body_factory: type[BaseModelFactory[Any]] | None,
) -> None:
    assert_response(
        mub_client.request(
            method=method,
            url=f"/mub/scheduler-service/events/{deleted_event_id}/",
            json=body_factory and body_factory.build_json(),
        ),
        expected_code=404,
        expected_json={"detail": "Event not found"},
    )
