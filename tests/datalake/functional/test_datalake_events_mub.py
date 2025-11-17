from unittest.mock import AsyncMock

import pytest
from starlette.testclient import TestClient

from app.common.schemas.datalake_sch import DatalakeEventInputSchema
from tests.common.assert_contains_ext import assert_nodata_response
from tests.datalake import factories

pytestmark = pytest.mark.anyio


async def test_queueing_datalake_event_recording(
    mub_client: TestClient,
    record_datalake_event_mock: AsyncMock,
) -> None:
    input_data: DatalakeEventInputSchema = factories.DatalakeEventInputFactory.build()

    assert_nodata_response(
        mub_client.post(
            "/mub/datalake-service/datalake-events/",
            json=input_data.model_dump(mode="json"),
        ),
    )

    record_datalake_event_mock.assert_awaited_once_with(input_data)
