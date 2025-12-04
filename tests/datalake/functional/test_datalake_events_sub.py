from uuid import UUID

import pytest
from pydantic_marshals.contains import assert_contains

from app.common.config_bdg import datalake_bridge
from app.common.schemas.datalake_sch import DatalakeEventInputSchema
from app.datalake.models.datalake_events_db import DatalakeEvent
from app.datalake.routes.datalake_events_sub import record_datalake_event
from tests.common.active_session import ActiveSession
from tests.datalake import factories

pytestmark = pytest.mark.anyio


async def test_datalake_event_recording(
    active_session: ActiveSession,
) -> None:
    input_data: DatalakeEventInputSchema = factories.DatalakeEventInputFactory.build()

    record_datalake_event.mock.reset_mock()

    await datalake_bridge.record_datalake_event(data=input_data)

    record_datalake_event.mock.assert_called_once_with(
        input_data.model_dump(mode="json")
    )

    async with active_session():
        datalake_event = await DatalakeEvent.find_first_by_kwargs(
            recorded_at=input_data.recorded_at
        )
        assert datalake_event is not None
        assert_contains(
            datalake_event,
            {
                "id": UUID,
                "kind": input_data.kind,
            },
        )
        await datalake_event.delete()
