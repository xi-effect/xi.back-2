import pytest

from app.scheduler.models.events_db import Event
from tests.common.active_session import ActiveSession
from tests.common.types import AnyJSON
from tests.scheduler import factories


@pytest.fixture()
async def event(
    active_session: ActiveSession,
) -> Event:
    async with active_session():
        return await Event.create(**factories.EventInputFactory.build_python())


@pytest.fixture()
async def event_data(
    event: Event,
) -> AnyJSON:
    return Event.ResponseSchema.model_validate(event).model_dump(mode="json")


@pytest.fixture()
async def deleted_event_id(active_session: ActiveSession, event: Event) -> int:
    async with active_session():
        await event.delete()
    return event.id
